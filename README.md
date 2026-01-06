# 1. What is AI Tutor? 

AITutor is a web-based platform that supports professors and universities in providing students with automated and AI-supported exercises. The system uses artificial intelligence for assessment and provides personalized feedback for students.


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

## 2.3 Start the application:

    uv run reflex run


# 3. Maintainance

## 3.1 Add dependencies:

    uv add <package-name>

This will add the dependency to `pyproject.toml`, update the `uv.lock` file and install the package to the project's virtual environment.


## 3.2 Migrate database after modifications:

    uv run reflex db makemigrations
    uv run reflex db migrate


# 4. Configuration
## 4.1 Application settings

The configuration is located in the file rxconfig.py.

Database URL: By default sqlite:///reflex.db

App name: “AITutor”

## 4.2 Privacy Notice
The privacy notice used on the website can be found in `aitutor/pages/legal_infos/datenschutz.md`. If you need to change it, you can edit this file.
A short version of this privacy notice is displayed on the register page. It can be modified in `aitutor/pages/legal_infos/datenschutz_short.md`

## 4.3 Further configurations
You need to add a "config.toml" file to the root directory of the project. 
This file should contain information about defaultusers, prompts and other configurations.
For more information about the config file, please refer to the [configfile documentation](docs/configfile.md).


# 5 Database management

The system uses Alembic to manage schema changes.

Create new migration:

    reflex db makemigrations
    refelx db migrate 


# 6. Tests

To ensure that the system works properly, tests are set up with pytest.

Execute tests:

    pytest


# 7. Run with Docker
This repository contains a docker compose setup for easy deployment. More information on how to use this docker setup can be found in [docker.md](docs/docker.md).


# 8. Architecture
see [architecture.md](docs/architecture.md) for more information about the architecture of the system.

# 9. License

All files in this package are provided under the AGPL v3 license, see
[LICENSE](./LICENSE).

Copyright © 2024 Eberhard Karls Universität Tübingen, Distributed
Intelligence/Autonomous Learning Group
