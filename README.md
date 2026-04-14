# AgentHazard

Static evaluation artifact for the paper _Mobile GUI Agents under Real-world Threats: Are We There Yet?_.

## What This Repository Contains

This repository reproduces the paper's **static environment** experiments. It evaluates mobile GUI agents on pre-collected scenarios with optional misleading content injected into screenshots at evaluation time.

Implemented agent backends:

- `m3a`
- `t3a`
- `autodroid`
- `uground`

Implemented API clients:

- `openai`
- `ark`
- `azure`
- `qwen`

## Repository Layout

- `src/agenthazard/cli/` — evaluation CLI
- `src/agenthazard/agent/` — agent prompting and output parsing
- `src/agenthazard/api/` — OpenAI-compatible async API clients
- `src/agenthazard/models.py` — scenario, task, UI element, and attack models
- `src/agenthazard/dataset.py` — dataset loader
- `scripts/` — convenience scripts for baseline and attack runs

## Setup

1. Install dependencies:

   ```bash
   uv sync --dev
   ```

2. Prepare the dataset under `data/`. The evaluator expects scenario folders containing:

   - `metadata.json`
   - `screenshot.jpg`
   - `original_vh.json`
   - `filtered_elements.json`

3. Copy the env template and configure API access:

   ```bash
   cp .env.local .env
   ```

   Set at least:

   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`

   For UGround-based experiments, also set:

   - `UG_API_KEY`
   - `UG_BASE_URL`

## Usage

Show the CLI help:

```bash
uv run python -m agenthazard.cli eval --help
```

Run a baseline evaluation:

```bash
uv run python -m agenthazard.cli eval \
  --data-dir data \
  --agent m3a \
  --client openai \
  --model gpt-4o-2024-11-20 \
  -o static_results/results-agent_m3a_model_gpt-4o-2024-11-20_baseline.parquet
```

Run an attack evaluation:

```bash
uv run python -m agenthazard.cli eval \
  --data-dir data \
  --agent m3a \
  --client openai \
  --model gpt-4o-2024-11-20 \
  --attack click \
  -o static_results/results-agent_m3a_model_gpt-4o-2024-11-20_attack_click.parquet
```

Batch scripts:

```bash
chmod +x scripts/*.sh
./scripts/eval-baseline.sh
./scripts/eval-attacks.sh
```

Results are stored as parquet files and support resume by default.

## Validation

Run the repository checks with:

```bash
uv run poe check
```
