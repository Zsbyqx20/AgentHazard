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

text_only_models=(
    "deepseek-r1-250528"
    "deepseek-v3-250324"
)

attacks=(
    "click"
    "status" # alias of "terminate"
)

for attack in "${attacks[@]}"; do
    for agent in "${agents[@]}"; do
        for model in "${full_models[@]}"; do
            echo "----------------------------------------"
            echo "Running: Agent=${agent}, Model=${model}, Attack=${attack}"

            uv run python -m agenthazard.cli eval \
                --data-dir data \
                --agent "$agent" \
                --client openai \
                --model "$model" \
                -o "static_results/results-agent_${agent}_model_${model}_attack_${attack}.parquet" \
                --attack "$attack"
            
            echo "Done: Agent=${agent}, Model=${model}, Attack=${attack}"
        done
    done

    for model in "${text_only_models[@]}"; do
        echo "----------------------------------------"
        echo "Running: Agent=t3a, Model=${model}, Attack=${attack}"

        uv run python -m agenthazard.cli eval \
            --data-dir data \
            --agent t3a \
            --client openai \
            --model "$model" \
            -o "static_results/results-agent_t3a_model_${model}_attack_${attack}.parquet" \
            --attack "$attack"
        
        echo "Done: Agent=t3a, Model=${model}, Attack=${attack}"
    done
done
