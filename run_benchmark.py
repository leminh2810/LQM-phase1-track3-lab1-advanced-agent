from __future__ import annotations
import json
import os
from pathlib import Path
import typer
from rich import print
from src.reflexion_lab.agents import ReActAgent, ReflexionAgent
from src.reflexion_lab.reporting import build_report, save_report
from src.reflexion_lab.schemas import RunRecord
from src.reflexion_lab.utils import load_dataset, save_jsonl
app = typer.Typer(add_completion=False)

@app.command()
def main(
    dataset: str = "data/hotpot_mini.json",
    out_dir: str = "outputs/sample_run",
    reflexion_attempts: int = 3,
    max_examples: int | None = None,
    agent: str = "both",
) -> None:
    examples = load_dataset(dataset)
    if max_examples is not None:
        examples = examples[:max_examples]
    react = ReActAgent()
    reflexion = ReflexionAgent(max_attempts=reflexion_attempts)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    react_path = out_path / "react_runs.jsonl"
    reflexion_path = out_path / "reflexion_runs.jsonl"
    mode = os.getenv("BENCHMARK_MODE", os.getenv("LLM_PROVIDER", "ollama"))
    dataset_name = Path(dataset).name

    if agent not in {"both", "react", "reflexion"}:
        raise typer.BadParameter("agent must be one of: both, react, reflexion")

    react_records = load_jsonl(react_path)
    reflexion_records = load_jsonl(reflexion_path)
    if agent in {"both", "react"}:
        react_records = run_with_checkpoints(react, examples, react_path, dataset_name, mode, out_path)
    if agent in {"both", "reflexion"}:
        reflexion_records = run_with_checkpoints(reflexion, examples, reflexion_path, dataset_name, mode, out_path)
    all_records = react_records + reflexion_records
    save_jsonl(react_path, react_records)
    save_jsonl(reflexion_path, reflexion_records)
    report = build_report(all_records, dataset_name=dataset_name, mode=mode)
    json_path, md_path = save_report(report, out_path)
    print(f"[green]Saved[/green] {json_path}")
    print(f"[green]Saved[/green] {md_path}")
    print(json.dumps(report.summary, indent=2))

def run_with_checkpoints(agent, examples, path: Path, dataset_name: str, mode: str, out_path: Path) -> list[RunRecord]:
    records = load_jsonl(path)
    completed = {record.qid for record in records}
    for example in examples:
        if example.qid in completed:
            continue
        record = agent.run(example)
        records.append(record)
        completed.add(record.qid)
        append_jsonl(path, record)
        save_report(build_report(load_jsonl(out_path / "react_runs.jsonl") + load_jsonl(out_path / "reflexion_runs.jsonl"), dataset_name=dataset_name, mode=mode), out_path)
        print(f"[cyan]{agent.agent_type}[/cyan] saved {len(records)}/{len(examples)}")
    return records

def load_jsonl(path: Path) -> list[RunRecord]:
    if not path.exists():
        return []
    records: list[RunRecord] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(RunRecord.model_validate_json(line))
    return records

def append_jsonl(path: Path, record: RunRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(record.model_dump_json() + "\n")

if __name__ == "__main__":
    app()
