# Contributing to AI Tutor

## Reflex configuration

The reflex configuration is located in the file rxconfig.py.

## Maintenance

### Add dependencies:

    uv add <package-name>

This will add the dependency to `pyproject.toml`, update the `uv.lock` file and install the package to the project's virtual environment.


### Migrate database after modifications:

    uv run reflex db makemigrations
    uv run reflex db migrate


## Architecture
If you are a new developer in the project, it may be helpful to first read the architecture documentation to get an overview of the system and its components.
See [architecture.md](docs/architecture.md) for more information about the architecture of the system.


## Tests

To ensure that the system works properly, tests are set up with pytest.
They can be found in the `tests` folder.

Execute tests:

    pytest