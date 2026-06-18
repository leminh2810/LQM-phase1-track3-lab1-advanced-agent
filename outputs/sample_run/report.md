# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini.json
- Mode: mock
- Records: 16
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.5 | 1.0 | 0.5 |
| Avg attempts | 1 | 1.5 | 0.5 |
| Avg token estimate | 55.88 | 98.88 | 43.0 |
| Avg latency (ms) | 1.25 | 1.5 | 0.25 |

## Failure modes
```json
{
  "by_agent": {
    "react": {
      "none": 4,
      "incomplete_multi_hop": 1,
      "wrong_final_answer": 1,
      "entity_drift": 2
    },
    "reflexion": {
      "none": 8
    }
  },
  "by_mode": {
    "none": 12,
    "incomplete_multi_hop": 1,
    "wrong_final_answer": 1,
    "entity_drift": 2
  },
  "analyzed_modes": [
    "entity_drift",
    "incomplete_multi_hop",
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
