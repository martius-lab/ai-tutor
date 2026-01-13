# What is AI Tutor? 

AI Tutor is a web-based platform that supports professors and universities in providing students with automated and AI-supported exercises. The students explain the question from the exercise to the AI agent. The AI then helps the student to understand the topic by asking questions and providing hints. Once the student thinks that the exercise is solved, a second AI agent checks the conversation and gives feedback on whether the exercise was solved correctly or not.
Tutors and admins have special roles to enable them to view the submitted conversations and give further feedback if necessary.


# Configuration
There are multiple configuration options available to customize the AI Tutor to your needs.

## Privacy Notice
The privacy notice used on the website can be found in `aitutor/pages/legal_infos/datenschutz.md`. If you need to change it, you can edit this file.
A short version of this privacy notice is displayed on the register page. It can be modified in `aitutor/pages/legal_infos/datenschutz_short.md`

## AI Tutor configuration
If you want to initialize the AI Tutor with some default information, you need to add a "config.toml" file to the root directory of the project. 
This file should contain information about defaultusers, prompts and other configurations.
For more information about the config file and its content, please refer to the [configfile documentation](docs/configfile.md).


# Installation

## Prerequisites

This project is managed with `uv`.  See [installation
instructions](https://docs.astral.sh/uv/getting-started/installation/).

After installing uv, run this command in the project root directory.

    uv run

When run for the first time, uv will automatically create a virtual environment in
`.venv` at the package root.
You can activate this venv normally but for the uv commands, that's actually not needed as long as uv is called from the projects root directory. So instead of activating the environment, you can also run commands like this:

    uv run <command>


## Setup

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

## Start the application:

To start the server in developer mode, run:

    uv run reflex run

For production mode, please refer to [docker.md](docs/docker.md) for more information.


# Run with Docker
This repository contains a docker compose setup for easy deployment. More information on how to use this docker setup can be found in [docker.md](docs/docker.md).

# Contributing
If you want to contribute to the project, please refer to the [contributing documentation](docs/contribute.md) for developer infos.

# License

All files in this package are provided under the AGPL v3 license, see
[LICENSE](./LICENSE).

Copyright © 2024 Eberhard Karls Universität Tübingen, Distributed
Intelligence/Autonomous Learning Group
