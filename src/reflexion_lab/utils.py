from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Iterable
from .schemas import ContextChunk, QAExample, RunRecord

def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

def load_dataset(path: str | Path) -> list[QAExample]:
    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return [normalize_example(item) for item in raw]

def normalize_example(item: dict[str, Any]) -> QAExample:
    if "qid" in item and "gold_answer" in item:
        return QAExample.model_validate(item)

    if "_id" in item and "answer" in item:
        supporting_titles = {title for title, _ in item.get("supporting_facts", [])}
        context_items = item.get("context", [])
        if supporting_titles:
            context_items = [chunk for chunk in context_items if chunk[0] in supporting_titles]
        return QAExample(
            qid=item["_id"],
            difficulty=normalize_difficulty(item.get("level", "medium")),
            question=item["question"],
            gold_answer=item["answer"],
            context=[
                ContextChunk(title=title, text=" ".join(sentences))
                for title, sentences in context_items
            ],
        )

    raise ValueError(f"Unsupported dataset example format: keys={sorted(item.keys())}")

def normalize_difficulty(value: str) -> str:
    value = value.strip().lower()
    if value in {"easy", "medium", "hard"}:
        return value
    return "medium"

def save_jsonl(path: str | Path, records: Iterable[RunRecord]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(record.model_dump_json() + "\n")
