# Contributing to AI Tutor

## Code style guide, formatting and linting

For Python code style, we follow [PEP 8](https://peps.python.org/pep-0008/).  The only
exception is the max. line length, where we use 88 (the default of `black` and `ruff
format`).

For code formatting, we use `ruff format`.  For linting and type checking we use `ruff
check` and `pyright`.  All of these are automatically checked on pull requests.
You can also run them locally:
```
uv run ruff format .
uv run ruff check .
uv run pyright .
```

Type hints should be added to all new functions so that `pyright` can do its work.
Note, however, that Reflex does weird things, which do not play well with type checkers,
so when dealing with Reflex, we need to add `# type: ignore` comments from time to time.


## Setup using uv

We use uv for managing the package.  See the README (section "Installation") on how to
use uv to initially set up and run the AI Tutor application.


## Reflex

We use [Reflex](https://reflex.dev) to build the application.  Reflex is a full-stack
framework that allows us to implement both the front end (i.e. the pages of the website)
and the back end (the functional logic) in Python.

Reflex does a lot of somewhat shady things to make this work.  If you are not familiar
with it, best go through the introductory part if its documentation first.
One of the most important aspects is that all data that is to be displayed in the front
end must be stored as variables in "state" classes (that is, classes that inherit from
`rx.State`).  Those variables can only be of basic types (str, int, list, dict, ...) or
dataclasses but not arbitrary objects.


## Architecture

If you are a new developer in the project, it may be helpful to first read the
architecture documentation to get an overview of the system and its components.
See [architecture.md](architecture.md) for more information about the architecture
of the system.


## Pull requests

All changes have to be submitted as pull request and have to be reviewed by at least one
maintainer.

To keep this process fast and reliable, please try to keep individual pull requests
short.  This can mean that the implementation of a larger feature should be split into
several steps, doing a separate pull request for each.


## Maintenance

### Add dependencies:

    uv add <package-name>

This will add the dependency to `pyproject.toml`, update the `uv.lock` file and install
the package to the project's virtual environment.


### Migrate database after modifications:

Database tables are defined as classes that are derived from `SQLModel` (see
`aitutor/models.py`).  Reflex uses [Alembic](https://alembic.sqlalchemy.org/en/latest/)
for dealing with changes on those models (so existing databases can be updated
accordingly when switching to a newer version of AI Tutor).  For this, the following two
commands need to be run:

1. **makemigrations:** This needs to be run once by the developer who changes an
   existing model or adds a new one.  It creates a new alembic file in
   `alembic/versions/`, which should be committed in the same commit that changed the
   model.
   ```
   uv run reflex db makemigrations
   ```

   In some cases, manual modifications have to be made to the migration
   file.  Most importantly, **if an existing table is modified**, add the following code
   snippet at the beginning of both the `upgrade` and the `downgrade` function:
   ```python
   # Need to disable foreign key constraints for SQLite.  SQLite recreates tables
   # for batch alters, and active foreign keys can trigger cascaded deletes.
   conn = op.get_bind()
   if conn.engine.name.startswith("sqlite"):
       conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
   ```
   This is needed as in SQLite tables are altered by deleting the old table and creating
   a new, modified one.  With foreign keys enabled, this can lead to unwanted cascaded
   deletes (aka **data loss**).

   Another typical modification that is needed: When adding boolean fields with default
   values, alembic does for some reason use `sa.text('0')`, which works for SQLite but
   not for PostgreSQL, which is strict regarding types.  So this needs to be changed
   manually to `sa.sql.false()` (or `true()` respectively).

   Finally, Alembic only takes care of changing the table definitions.  If any existing
   data needs to be converted/copied/etc., this has to be done by adding the appropriate
   SQL commands manually.  For an example, see `alembic/versions/cce41a34a7fa_.py`.

2. **migrate**:  This command uses the alembic migration scripts to update an existing
   database.  It needs to be run every time the code is updated (e.g. when pulling new
   changes from the main branch).
   ```
   uv run reflex db migrate
   ```

## Tests

We have some tests set up using [pytest](https://docs.pytest.org/en/stable/)
They can be found in the `tests` folder and are executed with
```
uv run pytest
```

When adding new features, it is always welcome to also add tests for them!
