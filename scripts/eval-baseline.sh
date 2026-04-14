#!/bin/bash
set -euo pipefail
mkdir -p static_results

agents=(
    "m3a"
    "t3a"
    "uground"
)

full_models=(
    "gpt-4o-2024-11-20"
    "gpt-4o-mini-2024-07-18"
    "gpt-5"
    "claude-4-sonnet"
)

for agent in "${agents[@]}"; do
    for model in "${full_models[@]}"; do
        echo "----------------------------------------"
        echo "Running: Agent=${agent}, Model=${model}"

        uv run python -m agenthazard.cli eval \
            --data-dir data \
            --agent "$agent" \
            --client openai \
            --model "$model" \
            -o "static_results/results-agent_${agent}_model_${model}_baseline.parquet"
        
        echo "Done: Agent=${agent}, Model=${model}"
    done
done

text_only_models=(
    "deepseek-r1-250528"
    "deepseek-v3-250324"
)

for model in "${text_only_models[@]}"; do
    echo "----------------------------------------"
    echo "Running: Agent=t3a, Model=${model}"

    uv run python -m agenthazard.cli eval \
        --data-dir data \
        --agent t3a \
        --client openai \
        --model "$model" \
        -o "static_results/results-agent_t3a_model_${model}_baseline.parquet"
    
    echo "Done: Agent=t3a, Model=${model}"
done
