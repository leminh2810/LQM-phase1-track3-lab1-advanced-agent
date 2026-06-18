from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
from typing import Literal
from .mock_runtime import FAILURE_MODE_BY_QID, actor_answer, base_qid, evaluator, reflector
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1
    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        for attempt_id in range(1, self.max_attempts + 1):
            started_at = perf_counter()
            answer = actor_answer(example, attempt_id, self.agent_type, reflection_memory)
            judge = evaluator(example, answer)
            latency_ms = max(1, round((perf_counter() - started_at) * 1000))
            token_estimate = self._estimate_tokens(example, answer, judge.reason, reflection_memory)
            trace = AttemptTrace(attempt_id=attempt_id, answer=answer, score=judge.score, reason=judge.reason, token_estimate=token_estimate, latency_ms=latency_ms)
            final_answer = answer
            final_score = judge.score
            if judge.score == 1:
                traces.append(trace)
                break
            
            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                reflection = reflector(example, attempt_id, judge)
                trace.reflection = reflection
                reflections.append(reflection)
                reflection_memory.append(
                    f"Attempt {attempt_id}: {reflection.lesson} Next strategy: {reflection.next_strategy}"
                )
            traces.append(trace)
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = "none" if final_score == 1 else FAILURE_MODE_BY_QID.get(base_qid(example.qid), "wrong_final_answer")
        return RunRecord(qid=example.qid, question=example.question, gold_answer=example.gold_answer, agent_type=self.agent_type, predicted_answer=final_answer, is_correct=bool(final_score), attempts=len(traces), token_estimate=total_tokens, latency_ms=total_latency, failure_mode=failure_mode, reflections=reflections, traces=traces)

    def _estimate_tokens(self, example: QAExample, answer: str, reason: str, reflection_memory: list[str]) -> int:
        """Approximate token use until a real LLM provider reports usage."""
        context_text = " ".join(f"{chunk.title} {chunk.text}" for chunk in example.context)
        prompt_text = " ".join([example.question, context_text, " ".join(reflection_memory), answer, reason])
        return max(1, round(len(prompt_text.split()) * 1.3))

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
