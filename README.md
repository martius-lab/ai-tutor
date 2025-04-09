# AI Tutor for learning lecture content 

AITandem is a web-based platform that supports professors and universities in providing students with automated and AI-supported exercises. The system uses artificial intelligence for assessment and provides personalized feedback for students.

## 2. System overview

The project is based on the Reflex framework and uses Python as the main programming language. Data is stored in a SQLite database, which can be replaced by another relational database system if required.

### 2.1 Architecture

Frontend: Reflex (generates UI from Python code)

Backend: Python-based, processes requests and evaluates solutions

Database: SQLite (standard), can be replaced by PostgreSQL or MySQL

AI modules: OpenAI API enables interaction with ChatGPT, but other AIs would also be possible


## 3. Installation

### Prerequisites

This project is managed with `uv`.  See [installation
instructions](https://docs.astral.sh/uv/getting-started/installation/).

When run for the first time, uv will automatically create a virtual environment in
`.venv` at the package root.
You can activate this venv normally but for the uv commands, that's actually not needed
as long as uv is called from the projects root directory.

### Setup

Clone the repository:

    git clone <URL-of-repository>
    cd aitandem

Initialize database:

    uv run reflex db init

Create local environment file `.env`:

```bash
OPENAI_API_KEY=<your key>
ADMIN_EMAIL=admin@mail.de
ADMIN_PW=very-strong-password
```
The admin email and password are used to auto-create an admin account for easy testing
during development.


### Start the application:

    uv run reflex run

## Maintainance

### Add dependencies:

    uv add <package-name>

This will add the dependency to `pyproject.toml`, update the `uv.lock` file and install
the package to the project's virtual environment.


### Migrate database after modifications:

    uv run reflex db makemigrations
    uv run reflex db migrate


## 4. Configuration

### 4.1 Application settings

The configuration is located in the file rxconfig.py.

Database URL: By default sqlite:///reflex.db

App name: “AITutor”

### 4.2 Customization of the AI modules

The AI components for grading exercises can be added or changed in separate modules.

## 5 Database management

The system uses Alembic to manage schema changes.

Create new migration:

reflex db makemigrations
refelx db migrate 

## 6. Tests

To ensure that the system works properly, tests are set up with pytest.

Execute tests:

pytest
