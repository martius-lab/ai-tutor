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

Signup welcome emails and password reset emails are sent through SMTP.
Configure the following values in `.env`:

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_FROM_EMAIL="AI Tutor <noreply@example.com>"
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT=10
AITUTOR_PUBLIC_URL=https://your-ai-tutor.example
```

`SMTP_USERNAME` and `SMTP_PASSWORD` are optional only if the SMTP server allows
unauthenticated sending.  If one is set, the other must be set as well.

For University of Tuebingen SMTP, the documented server is typically:

```
SMTP_HOST=smtpserv.uni-tuebingen.de
SMTP_PORT=587
SMTP_USE_TLS=true
```

The SMTP username may be the ZDV-ID rather than the visible email address.  In
that case, set `SMTP_USERNAME` to the ZDV-ID and set `SMTP_FROM_EMAIL` to the
actual sender address that should appear on account emails.

Password reset emails use `AITUTOR_PUBLIC_URL` to build reset links.  Set it to
the public URL users open in their browser.  New users receive a short welcome
email after registration.

Do not commit real SMTP credentials to the repository.


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
