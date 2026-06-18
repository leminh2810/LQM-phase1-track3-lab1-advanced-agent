from __future__ import annotations

import json
import os
import re
from time import sleep
from typing import Any
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from pydantic import ValidationError

from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .utils import normalize_answer

load_dotenv(encoding="utf-8-sig", override=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "120"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = os.getenv("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_TIMEOUT_SECONDS = int(os.getenv("GROQ_TIMEOUT_SECONDS", "120"))
GROQ_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "6"))
GROQ_MIN_DELAY_SECONDS = float(os.getenv("GROQ_MIN_DELAY_SECONDS", "0"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))

FAILURE_MODE_BY_QID = {
    "hp2": "incomplete_multi_hop",
    "hp4": "wrong_final_answer",
    "hp6": "entity_drift",
    "hp8": "entity_drift",
}


def base_qid(qid: str) -> str:
    return qid.split("_rep", 1)[0]


def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> str:
    user_prompt = "\n\n".join(
        [
            f"Question:\n{example.question}",
            f"Context:\n{format_context(example)}",
            f"Agent type: {agent_type}",
            f"Attempt: {attempt_id}",
            f"Reflection memory:\n{format_reflections(reflection_memory)}",
        ]
    )
    answer = llm_chat(ACTOR_SYSTEM, user_prompt).strip()
    return answer.strip('"').strip()


def evaluator(example: QAExample, answer: str) -> JudgeResult:
    if normalize_answer(example.gold_answer) == normalize_answer(answer):
        return JudgeResult(
            score=1,
            reason="Final answer matches the gold answer after normalization.",
        )

    user_prompt = "\n\n".join(
        [
            f"Question:\n{example.question}",
            f"Context:\n{format_context(example)}",
            f"Gold answer:\n{example.gold_answer}",
            f"Predicted answer:\n{answer}",
        ]
    )
    content = llm_chat(EVALUATOR_SYSTEM, user_prompt, json_mode=True)
    payload = extract_json_object(content)
    try:
        return JudgeResult.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Evaluator returned invalid JudgeResult JSON: {payload}") from exc


def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> ReflectionEntry:
    user_prompt = "\n\n".join(
        [
            f"Attempt id: {attempt_id}",
            f"Question:\n{example.question}",
            f"Context:\n{format_context(example)}",
            f"Evaluator feedback:\n{judge.model_dump_json()}",
        ]
    )
    content = llm_chat(REFLECTOR_SYSTEM, user_prompt, json_mode=True)
    payload = extract_json_object(content)
    payload.setdefault("attempt_id", attempt_id)
    try:
        return ReflectionEntry.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Reflector returned invalid ReflectionEntry JSON: {payload}") from exc


def llm_chat(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    if LLM_PROVIDER in {"groq", "grog"}:
        return groq_chat(system_prompt, user_prompt, json_mode=json_mode)
    if LLM_PROVIDER == "gemini":
        return gemini_chat(system_prompt, user_prompt, json_mode=json_mode)
    if LLM_PROVIDER == "ollama":
        return ollama_chat(system_prompt, user_prompt, json_mode=json_mode)
    raise ValueError(f"Unsupported LLM_PROVIDER={LLM_PROVIDER!r}. Use 'groq', 'gemini', or 'ollama'.")


def groq_chat(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    if not GROQ_API_KEY or GROQ_API_KEY == "PASTE_YOUR_GROQ_API_KEY_HERE":
        raise RuntimeError("Set GROQ_API_KEY in .env before running with LLM_PROVIDER=groq.")
    if not GROQ_API_KEY.startswith("gsk_"):
        raise RuntimeError("GROQ_API_KEY does not look like a Groq API key. It usually starts with 'gsk_'.")
    if GROQ_MIN_DELAY_SECONDS > 0:
        sleep(GROQ_MIN_DELAY_SECONDS)

    payload: dict[str, Any] = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    request = Request(
        GROQ_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "reflexion-lab/1.0",
        },
        method="POST",
    )

    raw: dict[str, Any] | None = None
    for retry_id in range(GROQ_MAX_RETRIES + 1):
        try:
            with urlopen(request, timeout=GROQ_TIMEOUT_SECONDS) as response:
                raw = json.loads(response.read().decode("utf-8"))
                break
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in {429, 500, 502, 503, 504, 520, 522, 524} and retry_id < GROQ_MAX_RETRIES:
                retry_after = exc.headers.get("retry-after") or parse_retry_after(detail)
                delay = float(retry_after) if retry_after else min(12.0, 1.5 * (retry_id + 1))
                sleep(delay)
                continue
            raise RuntimeError(f"Groq API returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError("Cannot reach Groq API. Check GROQ_API_KEY and internet access.") from exc

    if raw is None:
        raise RuntimeError("Groq API did not return a response.")

    try:
        return raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Groq response: {raw}") from exc


def gemini_chat(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "PASTE_YOUR_GEMINI_API_KEY_HERE":
        raise RuntimeError("Set GEMINI_API_KEY in .env before running with LLM_PROVIDER=gemini.")
    if not GEMINI_API_KEY.startswith("AIza"):
        raise RuntimeError(
            "GEMINI_API_KEY does not look like a Google AI Studio API key. "
            "Create one at https://aistudio.google.com/app/apikey; it usually starts with 'AIza'."
        )

    generation_config: dict[str, Any] = {
        "temperature": 0,
    }
    if json_mode:
        generation_config["response_mime_type"] = "application/json"

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}],
            }
        ],
        "generationConfig": generation_config,
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(GEMINI_MODEL, safe='')}:generateContent?key={quote(GEMINI_API_KEY, safe='')}"
    )
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=GEMINI_TIMEOUT_SECONDS) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError("Cannot reach Gemini API. Check GEMINI_API_KEY and internet access.") from exc

    try:
        return raw["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {raw}") from exc


def ollama_chat(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "temperature": 0,
        },
    }
    if json_mode:
        payload["format"] = "json"

    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(
            f"Cannot reach Ollama at {OLLAMA_URL}. Start Ollama and pull model {OLLAMA_MODEL!r} first."
        ) from exc

    try:
        return raw["message"]["content"]
    except KeyError as exc:
        raise RuntimeError(f"Unexpected Ollama response: {raw}") from exc


def extract_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Model did not return a JSON object: {text!r}")
        parsed = json.loads(text[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError(f"Model returned JSON, but not an object: {parsed!r}")
    return parsed


def parse_retry_after(text: str) -> str | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = {}
    value = payload.get("retry_after")
    if isinstance(value, (int, float, str)):
        return str(value)
    message = payload.get("error", {}).get("message", "")
    match = re.search(r"try again in (?:(?P<minutes>\d+(?:\.\d+)?)m)?(?P<seconds>\d+(?:\.\d+)?)s", message)
    if match:
        minutes = float(match.group("minutes") or 0)
        seconds = float(match.group("seconds") or 0)
        return str(minutes * 60 + seconds + 1)
    return None


def format_context(example: QAExample) -> str:
    return "\n".join(f"- {chunk.title}: {chunk.text}" for chunk in example.context)


def format_reflections(reflection_memory: list[str]) -> str:
    if not reflection_memory:
        return "None"
    return "\n".join(f"- {item}" for item in reflection_memory)
