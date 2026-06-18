# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_dev_distractor_v1.json
- Mode: groq
- Records: 34
- Agents: react

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.6471 | 0 | 0 |
| Avg attempts | 1 | 0 | 0 |
| Avg token estimate | 1198.03 | 0 | 0 |
| Avg latency (ms) | 335787.06 | 0 | 0 |

## Failure modes
```json
{
  "by_agent": {
    "react": {
      "none": 22,
      "wrong_final_answer": 12
    }
  },
  "by_mode": {
    "none": 22,
    "wrong_final_answer": 12
  },
  "analyzed_modes": [
    "wrong_final_answer"
  ]
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Reflexion helps when the first attempt stops after the first hop, drifts to a wrong second-hop entity, or returns a plausible but unsupported final answer. The reflection memory is useful because the next attempt receives a compact lesson about the failed reasoning path instead of repeating the same trajectory. The remaining risks are evaluator quality, overfitting to a reflection that is too specific, and higher latency or token cost from extra attempts.
