# Hadoop with Docker

Quick start for the Hadoop services using Docker Compose.

## Prerequisites

- Docker Desktop (or Docker Engine) with Docker Compose.

## Start

```sh
docker compose build
docker compose up -d
```

## Verify

- NameNode UI: http://localhost:9870
- ResourceManager UI: http://localhost:8088

## Stop

```sh
docker compose down
```

## Reset data (optional)

```sh
docker compose down -v
```
