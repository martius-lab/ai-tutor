# 1. What is AI Tutor? 

AITutor is a web-based platform that supports professors and universities in providing students with automated and AI-supported exercises. The students explain the question from the exercise to the ai agent. The ai then helps the student to understand the topic by asking questions and providing hints. Once the student thinks that the exercise is solved, a second ai agent checks the conversation and gives feedback on whether the exercise was solved correctly or not.
Tutors and admins have special roles to enable them to view the submitted conversations and give further feedback if necessary.


# 2. Installation

## 2.1 Prerequisites

This project is managed with `uv`.  See [installation
instructions](https://docs.astral.sh/uv/getting-started/installation/).

After installing uv, run this command in the project root directory.

    uv run

When run for the first time, uv will automatically create a virtual environment in
`.venv` at the package root.
You can activate this venv normally but for the uv commands, that's actually not needed as long as uv is called from the projects root directory. So instead of activating the environment, you can also run commands like this:

    uv run <command>


## 2.2 Setup

Clone the repository:

    git clone <URL-of-repository>
    cd aitutor

Initialize database:

    uv run reflex db init

Create local environment file `.env` with the following content:

```bash
OPENAI_API_KEY=<your key>
```

(Optional) Add your own `config.toml` file for the initial configuration. See [configfile documentation](docs/configfile.md) for more information.

## 2.3 Start the application:

To start the server in developer mode, run:

    uv run reflex run

For production mode, run:

    uv run reflex run --env prod


# 3. Configuration

## 3.1 Privacy Notice
The privacy notice used on the website can be found in `aitutor/pages/legal_infos/datenschutz.md`. If you need to change it, you can edit this file.
A short version of this privacy notice is displayed on the register page. It can be modified in `aitutor/pages/legal_infos/datenschutz_short.md`

## 3.2 AI Tutor configuration
If you want to initialize the AI Tutor with some default information, you need to add a "config.toml" file to the root directory of the project. 
This file should contain information about defaultusers, prompts and other configurations.
For more information about the config file and its content, please refer to the [configfile documentation](docs/configfile.md).

## 3.3 Reflex configuration

The reflex configuration is located in the file rxconfig.py.


# 4. Maintenance

## 4.1 Add dependencies:

    uv add <package-name>

This will add the dependency to `pyproject.toml`, update the `uv.lock` file and install the package to the project's virtual environment.


## 4.2 Migrate database after modifications:

    uv run reflex db makemigrations
    uv run reflex db migrate


# 5. Tests

To ensure that the system works properly, tests are set up with pytest.
They can be found in the `tests` folder.

Execute tests:

    pytest


# 6. Architecture
If you are a new developer in the project, it may be helpful to first read the architecture documentation to get an overview of the system and its components.
See [architecture.md](docs/architecture.md) for more information about the architecture of the system.


# 7. Run with Docker
This repository contains a docker compose setup for easy deployment. More information on how to use this docker setup can be found in [docker.md](docs/docker.md).

# 8. License

All files in this package are provided under the AGPL v3 license, see
[LICENSE](./LICENSE).

Copyright © 2024 Eberhard Karls Universität Tübingen, Distributed
Intelligence/Autonomous Learning Group
