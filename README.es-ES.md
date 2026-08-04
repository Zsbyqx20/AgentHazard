<h1>Agentes de GUI Móvil bajo Amenazas Realistas: ¿Ya Estamos Allí?</h1>

<center>

[![Static Badge](https://img.shields.io/badge/HomePage-green?style=plastic&logo=Homepage&logoColor=white)](https://agenthazard.github.io)
[![Static Badge](https://img.shields.io/badge/Paper-yellow?style=plastic&logo=DOI&logoColor=white)](https://doi.org/10.1145/3745756.3809249)
[![arXiv](https://img.shields.io/badge/arXiv-2507.04227-b31b1b.svg?style=plastic)](https://arxiv.org/abs/2507.04227)
[![Static Badge](https://img.shields.io/badge/github-Hijacking%20Tool-orange?style=plastic&logo=github)](https://github.com/Zsbyqx20/AWAttackerApplier)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?style=plastic&tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FZsbyqx20%2FAgentHazard%2Frefs%2Fheads%2Fmaster%2Fpyproject.toml&logo=Python&logoColor=white)
![GitHub Repo stars](https://img.shields.io/github/stars/Zsbyqx20/AgentHazard?style=plastic&logo=github)

![figure](assets/overview.webp)
</center>

## Lo Que Contiene Este Repositorio

Este repositorio reproduce los experimentos del **entorno estático** del artículo. Evalúa agentes de GUI móvil en escenarios pre-recopilados con contenido engañoso opcional inyectado en las capturas de pantalla durante la evaluación. Consulte nuestro artículo (**Apéndice A**) para más detalles y guía de reproducción.

Backend de agentes implementados:

| `m3a` | `t3a` | `autodroid` | `uground` |
| --- | --- | --- | --- |

## Estructura del Repositorio

- `src/agenthazard/cli/` — CLI de evaluación
- `src/agenthazard/agent/` — generación de instrucciones y análisis de salida de agentes
- `src/agenthazard/api/` — clientes API asíncronos compatibles con OpenAI
- `src/agenthazard/models.py` — modelos de escenario, tarea, elementos UI y ataque
- `src/agenthazard/dataset.py` — cargador de conjuntos de datos
- `scripts/` — scripts de conveniencia para ejecuciones de ataque y línea base

## Configuración

1. Instale las dependencias:

   ```bash
   uv sync --dev
   ```

2. Prepare el conjunto de datos en `data/` (disponible en [aquí](https://cloud.tsinghua.edu.cn/d/48ff830c185742b38c52/)). El evaluador espera carpetas de escenarios que contengan:

   - `metadata.json`
   - `screenshot.jpg`
   - `original_vh.json`
   - `filtered_elements.json`

3. Copie la plantilla de entorno y configure el acceso a la API:

   ```bash
   cp .env.local .env
   ```

   Configure al menos:

   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`

   Para experimentos basados en UGround, también configure:

   - `UG_API_KEY`
   - `UG_BASE_URL`

## Uso

Muestre la ayuda de la CLI:

```bash
uv run python -m agenthazard.cli eval --help
```

Ejecute una evaluación de línea base:

```bash
uv run python -m agenthazard.cli eval \
  --data-dir data \
  --agent m3a \
  --client openai \
  --model gpt-4o-2024-11-20 \
  -o static_results/results-agent_m3a_model_gpt-4o-2024-11-20_baseline.parquet
```

Ejecute una evaluación de ataque:

```bash
uv run python -m agenthazard.cli eval \
  --data-dir data \
  --agent m3a \
  --client openai \
  --model gpt-4o-2024-11-20 \
  --attack click \
  -o static_results/results-agent_m3a_model_gpt-4o-2024-11-20_attack_click.parquet
```

Scripts por lotes:

```bash
chmod +x scripts/*.sh
./scripts/eval-baseline.sh
./scripts/eval-attacks.sh
```

Los resultados se almacenan como archivos parquet y admiten reanudación por defecto.

## Validación

Ejecute las verificaciones del repositorio con:

```bash
uv run poe check
```
