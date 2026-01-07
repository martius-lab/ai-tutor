# Architecture

The project is based on the Reflex framework and uses Python as the main programming language.

Frontend: Reflex (generates UI from Python code)

Backend: Python-based, processes requests and evaluates solutions

Database: SQLite (standard), can be replaced by PostgreSQL or MySQL


## Pages

Every page has its own folder in `aitutor/pages/`. In this folder, you can find 4 files:
- `__init__.py`: Just for python to recognize this folder as a module
- `page.py`: This file contains the frontend function for the page. Here you need to use decorators to put the navigation bar on top of the page and to define which roles can access the page.
- `components.py`: This file contains all components that are used in the page
- `state.py`: This file contains the backend logic (state) needed for the page

To see how to add a new page to the app, have a look at the following commit. There a new template page was added:
Commit Hash: `83f36d6f44070c84bb0d8affd5577fadb17bad06`

## States
State files contain the functions that are used to process data and handle user interactions. These functions can be called from the frontend components.

A state usually always has these two functions:
- an `on_load()` function that is called when the page is loaded and therefore can be used to initialize variables. This function needs to be protected with the `@state_require_role_at_least(userrole)` decorator so that no data is loaded for unauthorized users.
- an `on_logout()` function to ensure that all user-specific data is cleared when the user logs out.

To keep the state classes readable for everyone, we always order its content in the following order:
- state variables
- setters for state variables
- on_load function
- on_logout function
- @rx.var functions
- regular functions

Information that is needed globally (e.g. the user language) is stored in the SessionState that is located in `aitutor/auth/state.py`. This state also handles the logout process. It has a function `global_load()` that should be called in every pages `on_load()` function to ensure that global data is consistent.

## Languages

We support multiple languages in the application. To do that, every string that is displayed to the user is stored in the file `language_state.py` in every supported language. To display a string, use the translate functions provided in the `language_state.py` file.

## Database Models
The database models are located in `aitutor/models.py`. Here, every class represents a table in the database. The attributes of the classes represent the columns of the tables.