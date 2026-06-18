# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini.json
- Mode: groq
- Records: 16
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.875 | 1.0 | 0.125 |
| Avg attempts | 1 | 1.25 | 0.25 |
| Avg token estimate | 86.38 | 143.62 | 57.24 |
| Avg latency (ms) | 1579.25 | 7061.25 | 5482.0 |

## Failure modes
```json
{
  "by_agent": {
    "react": {
      "none": 7,
      "entity_drift": 1
    },
    "reflexion": {
      "none": 8
    }
  },
  "by_mode": {
    "none": 15,
    "entity_drift": 1
  },
  "analyzed_modes": [
    "entity_drift"
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
