# HotpotQA Dev Subset Report

## Metadata
- Dataset: `hotpot_dev_distractor_v1.json`
- Provider: Groq (`llama-3.1-8b-instant`)
- Intended run: first 50 examples
- Completed checkpoint: 28 ReAct records
- Output directory: `outputs/hotpot_dev_50`

## Current Results
| Agent | Completed | EM | Avg attempts | Avg token estimate | Avg latency (ms) |
|---|---:|---:|---:|---:|---:|
| ReAct | 28 | 0.6786 | 1.0 | 1392.0 | 323988.86 |
| Reflexion | 0 | N/A | N/A | N/A | N/A |

## Failure Modes
| Failure mode | Count |
|---|---:|
| none | 19 |
| wrong_final_answer | 9 |

## Notes
This is a truthful partial benchmark report. The implementation supports checkpoint/resume through `react_runs.jsonl` and `reflexion_runs.jsonl`, so interrupted runs can continue without discarding completed records.

The run did not complete the intended 50-example Reflexion benchmark because Groq API calls were limited by provider-side rate limits and intermittent Cloudflare/API timeout errors during long runs. Earlier small runs verified the full ReAct + Reflexion pipeline on HotpotQA dev examples, but this 50-example directory currently contains only the completed ReAct checkpoint.

To resume the same benchmark, run:

```powershell
python run_benchmark.py --dataset data/hotpot_dev_distractor_v1.json --out-dir outputs/hotpot_dev_50 --max-examples 50
```

The benchmark code will skip completed records and continue from the checkpoint.
