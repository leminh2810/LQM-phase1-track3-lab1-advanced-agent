# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_golden.json
- Mode: groq
- Records: 40
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.75 | 0.95 | 0.2 |
| Avg attempts | 1 | 1.5 | 0.5 |
| Avg token estimate | 133.35 | 400.75 | 267.4 |
| Avg latency (ms) | 100667.4 | 231938.35 | 131270.95 |

## Failure modes
```json
{
  "by_agent": {
    "react": {
      "none": 15,
      "wrong_final_answer": 5
    },
    "reflexion": {
      "none": 19,
      "wrong_final_answer": 1
    }
  },
  "by_mode": {
    "none": 34,
    "wrong_final_answer": 6
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
