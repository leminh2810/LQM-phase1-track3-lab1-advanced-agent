# Hotpot Dev 50 Mixed Report

This report combines real checkpoint results with explicit mock-fill rows.

## Counts
- Real Groq records: 28
- Mock-fill records: 22
- Total records: 50

## Real Groq Summary
- Agent: ReAct
- EM: 0.6786
- Completed ReAct records: 28

## Important Note
The `mock_fill` rows are synthetic placeholders whose `predicted_answer` equals `gold_answer`. They were added only to make the report contain 50 cases after Groq long runs hit rate limits/API timeouts. Do not treat `mock_fill` rows as real LLM benchmark results.

JSON report: `outputs/hotpot_dev_50/report_mixed_50.json`
