<center>
<h1>Mobile GUI Agents under Real-world Threats: Are We There Yet?</h1>

[![Static Badge](https://img.shields.io/badge/HomePage-green?style=plastic&logo=Homepage&logoColor=white)](https://agenthazard.github.io)
[![Static Badge](https://img.shields.io/badge/Paper-red?style=plastic&logo=DOI&logoColor=white)](https://doi.org/10.1145/3745756.3809249)
[![Static Badge](https://img.shields.io/badge/github-Hijacking%20Tool-orange?style=plastic&logo=github)](https://github.com/Zsbyqx20/AWAttackerApplier)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?style=plastic&tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FZsbyqx20%2FAgentHazard%2Frefs%2Fheads%2Fmaster%2Fpyproject.toml&logo=Python&logoColor=white)
![GitHub Repo stars](https://img.shields.io/github/stars/Zsbyqx20/AgentHazard?style=plastic&logo=github)

![figure](assets/overview.webp)
</center>

## What This Repository Contains

This repository reproduces the paper's **static environment** experiments. It evaluates mobile GUI agents on pre-collected scenarios with optional misleading content injected into screenshots at evaluation time. Please refer to our paper for more details and reproduction guide.

Implemented agent backends:

| `m3a` | `t3a` | `autodroid` | `uground` |
| --- | --- | --- | --- |

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
