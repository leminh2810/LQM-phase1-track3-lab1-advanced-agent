# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_dev_distractor_v1.json
- Mode: groq
- Records: 6
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 1.0 | 0.6667 | -0.3333 |
| Avg attempts | 1 | 1.6667 | 0.6667 |
| Avg token estimate | 1284 | 4379.67 | 3095.67 |
| Avg latency (ms) | 12910.67 | 92604.67 | 79694.0 |

## Failure modes
```json
{
  "by_agent": {
    "react": {
      "none": 3
    },
    "reflexion": {
      "none": 2,
      "wrong_final_answer": 1
    }
  },
  "by_mode": {
    "none": 5,
    "wrong_final_answer": 1
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
