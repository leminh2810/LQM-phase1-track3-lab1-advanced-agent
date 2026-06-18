# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100_mock.json
- Mode: mock
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.5 | 1.0 | 0.5 |
| Avg attempts | 1 | 1.5 | 0.5 |
| Avg token estimate | 55.91 | 98.86 | 42.95 |
| Avg latency (ms) | 1 | 1.51 | 0.51 |

## Failure modes
```json
{
  "by_agent": {
    "react": {
      "none": 50,
      "incomplete_multi_hop": 13,
      "wrong_final_answer": 13,
      "entity_drift": 24
    },
    "reflexion": {
      "none": 100
    }
  },
  "by_mode": {
    "none": 150,
    "incomplete_multi_hop": 13,
    "wrong_final_answer": 13,
    "entity_drift": 24
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
