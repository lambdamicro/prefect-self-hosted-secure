# Prefect Self-Hosted Secure

## Introduction

This repository demonstrates how developers can self-host [Prefect](https://www.prefect.io/) (the open-source orchestration engine) and secure it using **basic authentication**. Prefect's open-source version gives you full control over your infrastructure — no cloud dependency, no usage limits. However, the default self-hosted setup exposes the API and UI without any authentication. This project shows a minimal, practical pattern for enabling basic auth so your Prefect server is not publicly accessible without credentials.

The stack is fully containerized with Docker Compose and includes Postgres for persistent storage, Redis for messaging, a Prefect server, background services, and a Docker-based worker pool — all wired together and ready to run locally.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                    │
│                                                     │
│  ┌──────────┐   ┌───────┐   ┌──────────────────┐  │
│  │ Postgres │   │ Redis │   │  prefect-server  │  │
│  │  (DB)    │   │(queue)│   │  (API + UI)      │  │
│  └──────────┘   └───────┘   └────────┬─────────┘  │
│                                       │             │
│                          ┌────────────┴──────────┐  │
│                          │   prefect-services    │  │
│                          │ (schedulers, events)  │  │
│                          └───────────────────────┘  │
│                                                     │
│  ┌─────────────────┐    ┌──────────────────────┐   │
│  │ prefect-worker  │    │      deployer         │   │
│  │ (docker pool)   │    │  (registers flows)    │   │
│  └─────────────────┘    └──────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

| Service | Description |
|---|---|
| `postgres` | Persistent database for Prefect state |
| `redis` | Message broker and cache for Prefect events |
| `prefect-server` | Hosts the Prefect API and UI on port `4200` |
| `prefect-services` | Runs background services (scheduler, event loop) |
| `prefect-worker` | Docker-type worker that executes flow runs |
| `deployer` | One-shot container that registers deployments on startup |

---

## Security: Basic Authentication

Prefect 3 supports basic authentication via two environment variables set in `.env` and passed to the relevant services:

```env
PREFECT_SERVER_API_AUTH_STRING="admin:pass"   # Enforced by the server
PREFECT_API_AUTH_STRING="admin:pass"          # Used by clients (workers, deployer)
```

- `PREFECT_SERVER_API_AUTH_STRING` — tells the Prefect server to require HTTP Basic Auth on all API requests.
- `PREFECT_API_AUTH_STRING` — tells Prefect clients (workers, CLI, deployer) what credentials to send when calling the API.

Both variables are loaded from `.env` via `env_file` in `docker-compose.yml`. This means the server rejects unauthenticated requests, and all internal services authenticate automatically using the same credentials.

> **Note:** Basic auth is a first layer of protection. For production, combine this with TLS (HTTPS) using a reverse proxy like Nginx or Traefik so credentials are not transmitted in plaintext.

---

## Project Structure

```
.
├── docker-compose.yml       # Full stack definition
├── Dockerfile.prefect       # Image used by the deployer and flow runs
├── prefect_deploy.py        # Registers deployments with the Prefect server
├── requirements.txt         # Python dependencies (prefect>=3.6.5)
├── .env                     # Environment config including auth credentials
└── jobs/
    └── test-env-vars.py     # Example flow: reads and logs env vars
```

---

## Services Deep Dive

### `prefect-server`

Runs the Prefect API and UI with `--no-services` so background tasks are handled by a dedicated container. Key settings:

- Connected to Postgres via `asyncpg`
- Uses Redis as the messaging broker and cache
- Basic auth enforced via `PREFECT_SERVER_API_AUTH_STRING`
- UI accessible at `http://localhost:4200`

### `prefect-services`

Runs `prefect server services start` separately. This handles event-driven scheduling, automation triggers, and other background loops. It connects to the same Postgres and Redis instances as the server.

### `prefect-worker`

Polls the `local-pool` work pool and executes flow runs as Docker containers. It:

- Installs `prefect-docker` at startup
- Mounts the Docker socket to spin up sibling containers
- Uses `host.docker.internal` to reach the Prefect API on the host network

### `deployer`

A one-shot service that:
1. Creates the `local-pool` work pool (Docker type) if it does not already exist
2. Runs `prefect_deploy.py` to register all deployments

It exits after completion (`restart: "no"`).

---

## Example Flow: `jobs/test-env-vars.py`

A simple flow used to validate that environment variables are correctly injected into flow run containers.

```python
@flow
async def start_test():
    logger = get_run_logger()
    environment = os.getenv("ENVIRONMENT")

    if environment:
        logger.info(f"ENVIRONMENT variable is set to: {environment}")
    else:
        logger.warning("ENVIRONMENT variable is not set")

    for i in range(5):
        log_iteration(i)
```

- Reads the `ENVIRONMENT` variable and logs its value
- Runs 5 sequential task iterations with a 2-second delay each
- Useful for confirming that `job_variables.env` in the deployment config is working

---

## Deployment Registration: `prefect_deploy.py`

Deployments are defined programmatically and registered against the running server:

```python
DEPLOYMENTS = [
    ("jobs/test-env-vars.py:start_test", "start-test-env-vars-flow"),
]
```

Each flow is loaded from the local directory (or optionally from a Git repo) and deployed to the `local-pool` work pool using the pre-built `getting-started-flow:v1` image. Job variables inject the `ENVIRONMENT` variable into each flow run container.

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Docker daemon running locally

### 1. Configure credentials

Edit `.env` to set your desired username and password:

```env
ENVIRONMENT=local.dev
PREFECT_SERVER_API_AUTH_STRING="admin:yourpassword"
PREFECT_API_AUTH_STRING="admin:yourpassword"
```

### 2. Build and start the stack

```bash
docker compose up --build
```

The `deployer` service will register the example flow automatically. Once it exits, the worker is ready to pick up runs.

### 3. Open the UI

Navigate to `http://localhost:4200`. You will be prompted for the credentials set in `.env`.

### 4. Trigger a flow run

From the UI, find `start-test-env-vars-flow` under Deployments and click **Run**.

Alternatively, using the CLI with auth:

```bash
PREFECT_API_URL=http://localhost:4200/api \
PREFECT_API_AUTH_STRING="admin:yourpassword" \
prefect deployment run 'start-test/start-test-env-vars-flow'
```

---

## Resetting the Environment

To wipe all containers, images, and volumes and start fresh:

```bash
docker system prune -a --volumes --force
```

> This removes **all** Docker data on your machine, not just this project. Use with caution.

---

## Dependencies

| Package | Version |
|---|---|
| `prefect` | `>=3.6.5` |
| `prefect-docker` | Installed at worker startup |
| `prefect-redis` | Pulled in with Prefect server image |
