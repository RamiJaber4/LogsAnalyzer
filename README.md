# Log Analyzer

A small system that ingests raw log lines, processes them asynchronously via a queue/worker,
stores aggregated metrics in MySQL, and exposes them through a FastAPI backend with a simple
HTML/JS frontend (served via a lightweight Python proxy).

## Architecture

```
Browser (frontend/index.html)
        │
        ▼
frontend_server.py  (proxy on :8001)
        │  /api/*
        ▼
FastAPI app.py  (backend on :8000)
        │
        ├── queue_manager.py  (asyncio.Queue)
        │        │
        │        ▼
        │   worker.py  (background task, batches of 5 logs)
        │        │
        │        ▼
        │   processing_logs.py  (LogParser, MetricsCalculator)
        │
        ▼
database.py  (MySQL connection pool)
        │
        ▼
MySQL (init.sql: metrics, component_stats tables)
```

## Components

- **app.py** — FastAPI application. Endpoints:
  - `POST /recieve-log` — accepts raw text log lines, pushes them onto the async queue.
  - `GET /show-stats` — returns aggregated totals (requests, errors, avg response).
  - `GET /show-comp-stats` — returns per-component stats.
  - `POST /reset-metrics` — resets all metrics to zero.
  - `GET /health` — health check.
- **worker.py** — background task that pulls logs off the queue, updates the in-memory
  `MetricsCalculator`, and flushes to MySQL every 5 logs.
- **processing_logs.py** — log parsing (`LogParser`) and metrics aggregation (`MetricsCalculator`,
  `ComponentManager`). Recognized components: `auth`, `payment`, `database`, `rate-limiter`.
- **database.py** — `DatabaseManager` wrapping a MySQL connection pool (get/update metrics,
  get/update component stats, reset).
- **queue_manager.py** — shared `asyncio.Queue` instance.
- **frontend/** — static HTML/JS UI + a small Python proxy server (`frontend_server.py`) that
  forwards `/api/*` requests to the backend, so the browser only ever talks to one origin.

## Log format

Each log line is comma-separated (split into at most 5 fields):

```
<timestamp>,<level>,<component>,<response_time_ms>,<message>
```

Example:
```
2026-07-16T12:00:00Z,info,auth,105,User login successful
2026-07-16T12:01:43Z,error,database,240,Failed query
```

## Database schema

Defined in `init.sql`, created automatically on the first `db` container boot.

```
┌───────────────────────────┐        ┌────────────────────────────────┐
│         metrics           │        │        component_stats          │
├───────────────────────────┤        ├────────────────────────────────┤
│ id             INT  PK AI  │        │ component      VARCHAR(50) PK  │
│ total_requests INT         │        │ requests       INT             │
│ error          INT         │        │ errors         INT             │
│ avg_response   DOUBLE      │        │ avg_response   DOUBLE          │
└───────────────────────────┘        └────────────────────────────────┘
   single-row table:                    one row per component:
   global aggregate totals              auth / payment / database / rate-limiter
```

- **metrics** — one logical row holding the running totals across *all* logs
  (`total_requests`, `error`, `avg_response`). Updated by `DatabaseManager.update_metric`.
- **component_stats** — one row per known component (`auth`, `payment`, `database`,
  `rate-limiter`), each with its own `requests`, `errors`, `avg_response`. Updated by
  `DatabaseManager.update_component`. Unrecognized components are ignored by
  `MetricsCalculator.process_log` (logged as a warning) and never reach this table.

Both tables are updated together by `worker.py` every 5 processed logs, and both are reset
to zero via `POST /reset-metrics`.

## Running with Docker Compose

1. Copy `.env.example` to `.env` and fill in your own values (see below).
2. Build and start everything:
   ```bash
   docker compose up --build
   ```
3. Services:
   - Backend: http://localhost:8000
   - Frontend: http://localhost:8001
   - MySQL: localhost:3306

## Environment variables

See `.env.example` for the full list. Required:

| Variable | Description |
|---|---|
| `MYSQL_ROOT_PASSWORD` | MySQL root password |
| `MYSQL_DB_NAME` | Database name created on first boot |
| `MYSQL_DB_USER` / `MYSQL_DB_PASSWORD` | App-level DB user |
| `DB_HOST` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | Used by the FastAPI app to connect |

**Never commit your real `.env` file.** It's excluded via `.gitignore`; only `.env.example`
(with placeholder values) should be tracked in git.

## Running locally without Docker

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

In a separate terminal:
```bash
python frontend/frontend_server.py
```

## Notes

- Sample log data lives in `samples/logs.log` (contains duplicate lines by design, useful for
  testing aggregation) — it's not meant to represent real production data.

