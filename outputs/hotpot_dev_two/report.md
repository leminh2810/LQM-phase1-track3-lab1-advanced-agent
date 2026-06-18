# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_dev_distractor_v1.json
- Mode: groq
- Records: 4
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 1.0 | 1.0 | 0.0 |
| Avg attempts | 1 | 1.5 | 0.5 |
| Avg token estimate | 1193.5 | 3105 | 1911.5 |
| Avg latency (ms) | 25446 | 56841 | 31395 |

## Failure modes
```json
{
  "by_agent": {
    "react": {
      "none": 2
    },
    "reflexion": {
      "none": 2
    }
  },
  "by_mode": {
    "none": 4
  },
  "analyzed_modes": []
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Reflexion helps when the first attempt stops after the first hop, drifts to a wrong second-hop entity, or returns a plausible but unsupported final answer. The reflection memory is useful because the next attempt receives a compact lesson about the failed reasoning path instead of repeating the same trajectory. The remaining risks are evaluator quality, overfitting to a reflection that is too specific, and higher latency or token cost from extra attempts.
