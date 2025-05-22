# Hijacking JARVIS: Benchmarking Mobile GUI Agents against Unprivileged Third Parties

<p align="center">
  <a href="https://agenthazard.github.io">🏠 Project Page</a> |
  <a href="https://github.com/Zsbyqx20/AWAttackerApplier">🛠️ Hijacking Tool</a>  |
  <a href="https://cloud.tsinghua.edu.cn/f/8a26e3521fbb4047bc36/">📃 Paper</a>
</p>

![intro](assets/pipeline.png)

> This repository contains code & data for the paper: "Hijacking JARVIS:
> Benchmarking Mobile GUI Agents against Unprivileged Third Parties".

## ⚙️ Project Setup

Please clone the project first.

```bash
$ git clone https://github.com/Zsbyqx20/AgentHazard.git
```

### Virtual Environment

It is recommended to use [uv](https://docs.astral.sh/uv/) for setting up the
dependencies of this project.

```bash
$ uv sync --no-dev
```

It is also okay to use your preferred dependency manager through
`requirements.txt`.

```bash
$ pip install -r requirements.txt
```

### Data Download

You can get access to our dynamic & static dataset through this
[link](https://cloud.tsinghua.edu.cn/f/392e8053a8a5494a8afb/?dl=1), or the
commands below:

```bash
$ wget "https://cloud.tsinghua.edu.cn/f/392e8053a8a5494a8afb/?dl=1" -O data.tar.gz
$ mv data.tar.gz /path/to/the/repository
$ tar xzf data.tar.gz
```

After decompress the file, please ensure the structure of the folders:

```
├── data
│   ├── dynamic
│   └── static
└── src
    └── agenthazard
        └── ...
```

## 📈 Run Evaluations

### Dynamic Dataset

We use jinja template to manage and generate configurations for the
[hijacking tool](https://github.com/Zsbyqx20/AWAttackerApplier). Please download
the latest release and install it on your AVD.

In order to convert the jinja files into JSON files, just run:

```bash
# if you are using uv
$ ah generate

# if you are using other dependency manager
$ python -m agenthazard.cli generate
```

After that, please clone our customized Android World repository, and put the
generated JSON files into the `config` folder.

> Here the `config` folder refers to `AndroidWorld` instead of the current
> repository.

```bash
$ git clone https://github.com/Zsbyqx20/android_world.git
```

You need to follow the instructions of Android World to set up environments and
AVDs. Here is an example.

```bash
python run.py \
  --suite_family=android_world \
  --agent_name=t3a_gpt4 \
  --perform_emulator_setup \
  --tasks=ContactsAddContact,ClockStopWatchRunning \
  --attack_config config/xxxxx.json \ # specify the configuration path here
  --break_on_misleading_actions # if specified, the program will quit when a misleading action is detected.
```

> Note: to keep the consistency among all runs, we recommend you to save a
> checkpoint after you just finishing configurations of a fresh AVD. Refer to
> the `eval` folder under the Android World project to check more details on how
> to automatically run evaluations. We provide a solution on robust mechanisms
> including automatic reloading states when meeting an error and restarting AVDs
> if needed.

### Static Dataset

The static part of our dataset is under the `data/static/` folder. Each scenario
contains 4 files, namely `screenshot.jpg`, `filtered_elements.json`,
`metadata.json`, and `original_vh.json`. The detailed logic can be found at
`src/agenthazard/dataset.py`.

For evaluation, you are required to set your API key in the `.env` file. You may
refer to `.env.local` file as an example, and refer to
`src/agenthazard/api/client` for more clients available, or customizing your own
LLM client.

```env
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://xxxx.com
```

We provide convenient evaluation entries through the `eval` command:

```bash
# if you are using uv
$ ah eval --help 

# if you are using other dependency manager
$ python -m agenthazard.cli eval --help
```

For each modality of the agent, we choose M3A, T3A and UGround (to be released)
to implement for evaluation logic. We support to choose from different agents,
different LLMs, as well as different misleading actions as settings.

Please check our paper for more details.
