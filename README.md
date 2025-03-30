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

### 3.1 Prerequisites

Python ≥ 3.9

Virtual environment (recommended)

Reflex Framework

Alembic for database migrations 

### 3.2 Setup

Clone the repository:
git clone <URL-of-repository>
cd aitandem

### reate & activate virtual environment:
python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows

### Install dependencies:

pip install -r requirements.txt

### Initialize database:

reflex db init
reflex db makemigrations
reflex db migrate 

## Create environment file
need .env file with variables:
```bash 
OPENAI_API_KEY
ADMIN_EMAIL
ADMIN_PW
```

### Start the application:

```bash 
reflex run
```

## Maintainance: update requirements from pyproject.toml
require pip-tools to be installed
```bash
pip-compile --output-file=requirements.txt pyproject.toml
```

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
