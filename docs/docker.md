# Run with Docker

This repository contains a Docker Compose setup for easy deployment.  This is based on
one of the [examples in the Reflex
repo](https://github.com/reflex-dev/reflex/tree/main/docker-example/production-compose).

The basic `compose.yaml` only starts the Reflex application.  With the additional
`compose.prod.yaml`, a PostgreSQL database is used instead of SQLite and Redis server
for something related to the front end, which the author of this text never fully
understood...


## Basic usage

A `Makefile` is provided for the most basic tasks.  The following commands have to be
called from the root directory of the package.  See the Makefile itself for the actual
docker commands which are called.

A `.env` file (see section "Configuration" below) is expected to be found in the
projects root directory and is mounted into the container from the host system.  This
means that the configuration can easily be changed without the need of rebuilding the
images.


**Build the container:**

```
# make build
```

**Start production setup with PostgreSQL:**

```
# make up
```
When testing locally, open [https://localhost](https://localhost) in your browser to
access the application.

**Stop everything:**

```
# make down
```

**View the logs:**

```
# make logs
```


## Configuration

### .env

The `.env` file contains additional configuration, which cannot be changed in the
AI-Tutor UI.  Below is an example with explanation of the individual variables.  All
variables are required unless explicitly specified otherwise.

```sh
# The domain of the server on which AI-Tutor is running.  Use 'localhost' for local
# testing
DOMAIN=ai-tutor.example.de

# API key for the LLM access
OPENAI_API_KEY=<secret key>
# [Optional] Base URL for the OpenAI API.  Set this when using a model provider other
# than OpenAI.  If not set, OpenAI is used.
OPENAI_BASE_URL=example-ai-company.com

# Password for the PostgreSQL database (will be used when creating the database if it
# doesn't exist yet).
POSTGRES_PASSWORD=<secret password>

# [Optional] SMTP settings for sending emails.  If not set, emails are printed to stdout
# (only use this for local testing).
# The example values below assume that the host has postfix configured for sending
# emails and that the IP of the docker0 interface is 172.17.0.1.
SMTP_HOST=172.17.0.1
SMTP_PORT=25
SMTP_FROM_EMAIL="noreply@ai-tutor.cs.uni-tuebingen.de"
SMTP_USE_TLS=false
SMTP_USE_SSL=false
SMTP_TIMEOUT=10
# Credentials if the SMTP server requires authentication
#SMTP_USERNAME=your-smtp-user
#SMTP_PASSWORD=your-smtp-password

# [Optional] The subnet used by the docker containers.  This is explicitly set to
configuration of postfix on the host easier.  It defaults to 172.18.0.0/16.  In case
that range is already used, you may specify a different range here.
AITUTOR_DOCKER_SUBNET=172.22.0.0/16
```

**Local testing with emails:**  To test sending of emails locally (during development),
you may run Mailpit using

```
# docker compose -f compose.mailpit.yaml up -d
```

and configure SMTP settings as follows:


```
SMTP_HOST=mailpit
SMTP_PORT=1025
SMTP_FROM_EMAIL="AI Tutor <noreply@example.com>"
SMTP_USE_TLS=false
SMTP_USE_SSL=false
```

Open [http://localhost:8025](http://localhost:8025) to inspect captured emails.
