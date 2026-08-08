# Run with Docker

This repository contains a docker compose setup for easy deployment.  This is based on
one of the [examples in the Reflex
repo](https://github.com/reflex-dev/reflex/tree/main/docker-example/production-compose).

## Basic usage

To test locally, simply run (from the projects root directory)
```
COMPOSE_BAKE=true docker compose build
```
to build images using the current state of the code and run with
```
# with sqlite
docker compose up
```

Then open [https://localhost](https://localhost) in your browser to access the application.

The config files `config.toml` and `.env` are expected to be found in the projects root directory and are mounted into the container from the host system.  This means that the configuration can easily be changed without the need of rebuilding the images.

## Email setup

Signup welcome emails are sent through SMTP.  Configure the following values in
`.env`:

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_FROM_EMAIL="AI Tutor <noreply@example.com>"
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT=10
DOMAIN=your-ai-tutor.example
```

`SMTP_USERNAME` and `SMTP_PASSWORD` are optional only if the SMTP server allows
unauthenticated sending.  If one is set, the other must be set as well.

Signup welcome emails use `DOMAIN` to build HTTPS login links.  Set it to the
public domain users open in their browser.

Do not commit real SMTP credentials to the repository.

For local email testing without sending real mail, configure the app container
to send signup emails to Mailpit:

```
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_FROM_EMAIL="AI Tutor <noreply@example.test>"
SMTP_USE_TLS=false
SMTP_USE_SSL=false
DOMAIN=localhost
```

Leave `SMTP_USERNAME` and `SMTP_PASSWORD` unset unless you configure Mailpit to
require authentication.

Then start the optional Mailpit compose override:

```
docker compose -f compose.yaml -f compose.mailpit.yaml up
```

Open [http://localhost:8025](http://localhost:8025) to inspect captured emails.


## Production environment with Postgresql

```
docker compose -f compose.yaml -f compose.prod.yaml up

# or to add additional debug tools
docker compose -f compose.yaml -f compose.prod.yaml -f compose.tools.yaml up
```
You can then access it locally on `https://localhost`.

Note that for Postgresql, a password needs to be set using `POSTGRES_PASSWORD`
in the `.env` file.

## On the server

To deploy on a server
- Copy the project code and config files (`config.toml` and `.env`) to the
  server
- Add `DOMAIN=your-domain.com` to `.env`
- Build the images
  ```
  COMPOSE_BAKE=true docker compose build
  ```
- Run in production mode:
  ```
  docker compose -f compose.yaml -f compose.prod.yaml up -d
  ```
  The `-d` flag detaches the process from the terminal.  You can view the
  output with
  ```
  docker compose -f compose.yaml -f compose.prod.yaml logs
  ```
- To shut it down:
  ```
  docker compose -f compose.yaml -f compose.prod.yaml down
  ```
