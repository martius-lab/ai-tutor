# Basic commands for starting/stopping the application via docker
.PHONY: build up down logs app-logs

build:
	COMPOSE_BAKE=1 docker compose -f compose.prod.yaml build

up:
	docker compose -f compose.prod.yaml up -d

down:
	docker compose -f compose.prod.yaml down

logs:
	docker compose -f compose.prod.yaml logs -ft

app-logs:
	docker compose -f compose.prod.yaml logs -ft app
