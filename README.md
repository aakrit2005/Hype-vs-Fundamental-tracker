# Hype vs Fundamentals Tracker
A full-stack research platform that measures the gap between public attention
(hype) and fundamental quality for a universe of stocks, then rigorously
tests whether that gap has any measurable relationship with future returns.

Most stock-screening tools show you price. This one shows you the distance
between what the market is *talking about* and what the business is actually
*doing*, and then publishes its own backtest so you can judge whether that
distance means anything.

> **Disclaimer:** This project is an educational research tool. It is not
> investment advice, and nothing in this repository or its deployed
> instances should be used as the basis for buying or selling securities.

---

## Table of Contents

- [The Signal](#the-signal)
- [Validation Methodology](#validation-methodology)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Local Setup](#local-setup)
- [Daily Pipeline](#daily-pipeline)
- [Sentiment Classifier Upgrade](#sentiment-classifier-upgrade)
- [Testing and CI](#testing-and-ci)
- [Docker](#docker)
- [Deployment and Monitoring](#deployment-and-monitoring)
- [Project Status](#project-status)
- [Judging Whether the Signal Is Real](#judging-whether-the-signal-is-real)

---

## The Signal

For each ticker, every trading day, the system produces three numbers and
one quality flag.

### Hype Score (0–100)

    hype = 100 × (0.70 × volume_norm + 0.30 × sentiment_norm)

- `volume_norm`: daily news result volume, min-max normalized across the
  tracked universe for that day.
- `sentiment_norm`: headline sentiment mapped from [-1, 1] to [0, 1].
- Min-max normalization is used deliberately instead of z-scores: with a
  universe of 6–50 tickers, z-scores overreact to single outliers.

### Fundamentals Score (0–100)

    fund = 100 × (0.50 × pe_score + 0.50 × eps_score)

- `pe_score`: P/E made **sector-relative** (ticker P/E divided by the sector
  median P/E, clamped to [0, 3]), then min-max normalized and inverted, so
  cheaper-than-peers scores higher. Sectors with fewer than two peers fall
  back to the universe median. Negative P/E is treated as maximally weak.
- `eps_score`: quarterly EPS growth, min-max normalized, higher is better.

A raw P/E of 35 means nothing in isolation. Against a sector median of 20 it
means something. That comparison is the point.

### Divergence Gap

    gap = hype − fund

- Large positive: heavy attention on weak fundamentals (overhyped).
- Large negative: strong fundamentals with little attention (underhyped).

### Confidence Flag (0.05–1.0)

Starts at 1.0 and is penalized for weak evidence:

| Condition | Penalty |
|---|---|
| Missing or zero news volume | −0.30 |
| News volume below 5 | −0.15 |
| Missing sentiment | −0.10 |
| Missing P/E | −0.25 |
| Negative P/E | −0.10 |
| Missing EPS growth | −0.25 |
| Fewer than 2 sector peers | −0.15 |
| Universe smaller than 5 tickers | −0.10 |

Thinly-traded tickers and low-attention days visibly degrade confidence
instead of silently producing a misleading number. Alerting ignores any
score below 0.5.

---

## Validation Methodology

The system does not ask you to trust the signal. It tests it.

- Historical adjusted-close prices are stored per ticker per day.
- For each stored score, the entry price is the last trading day on or
  before the score date; the exit price is `horizon` trading days later.
- The **information coefficient (IC)** is the Spearman rank correlation
  between the divergence gap and the realized forward return, computed for
  5-day and 20-day horizons. Pearson correlation is stored alongside.
- Returns are also split by gap direction (positive vs negative gap) so an
  asymmetric effect cannot hide inside a single correlation number.
- Every backtest run is persisted with its sample size and notes, and the
  frontend's Signal Report page charts IC over time.

Interpretation guide for a daily cross-sectional signal:

| IC | Reading |
|---|---|
| ≈ 0 | No measurable edge; the gap is a visualization, not a signal |
| 0.03 – 0.05 | Weak but interesting; keep collecting data |
| > 0.05 sustained, n in the hundreds | A real result worth publishing |

Transaction costs, slippage and borrow fees are **not** modeled. A positive
IC below the cost threshold is still not a tradeable strategy.

---

## Features

- Divergence leaderboard with sortable columns, search, over/underhyped
  filter and CSV export
- Live lookup for any symbol: fetch, score and display in one request,
  rate-limited to protect API quota
- Ticker detail with hype-vs-fundamentals history chart and per-ticker
  backtest summary
- Public Signal Report page publishing methodology and IC history
- Per-user watchlists with in-app alerts when |gap| crosses a threshold
- JWT authentication, bcrypt password hashing
- Retrying API clients with exponential backoff and persistent quota
  tracking per provider per day
- Idempotent ingestion: rerunning any day never duplicates a row
- Pluggable sentiment: word-list lexicon by default, FinBERT
  (financial-headline classifier) as an opt-in upgrade that rescores all
  history without refetching paid data
- Structured JSON logging in production, Sentry hook, `/healthz` endpoint
- Docker Compose stack with Postgres; SQLite for zero-setup development
- CI on every push: backend lint + tests, frontend type-check + build
- Test suite that never touches real APIs (mocked HTTP transport, faked
  yfinance), so CI cannot burn quota

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.10+, FastAPI, SQLAlchemy 2 (async), Pydantic v2 |
| Databases | SQLite (dev), Postgres via asyncpg (Docker / production) |
| Data sources | SerpAPI Google News, yfinance |
| Sentiment | Lexicon baseline; ProsusAI/finbert optional |
| Auth | JWT (PyJWT), bcrypt |
| Frontend | React 18, TypeScript, Vite, React Router, Chart.js |
| Testing | pytest, pytest-asyncio, httpx MockTransport, ruff |
| CI/CD | GitHub Actions |
| Containers | Docker, Docker Compose (Postgres 16, nginx) |
| Monitoring | Structured logs, Sentry, uptime check on /healthz |

---

## Architecture

    hype-fundamentals-tracker/
    ├── .github/workflows/ci.yml      # lint + test + build on every push
    ├── docker-compose.yml            # postgres + backend + frontend
    ├── backend/
    │   ├── app/
    │   │   ├── main.py               # app factory, CORS, logging middleware, healthz
    │   │   ├── api/v1/               # routers: auth, tickers, signals, backtest, watchlist, alerts
    │   │   ├── core/                 # config, database, security, logging, init_db
    │   │   ├── models/               # 10 SQLAlchemy tables
    │   │   ├── schemas/              # Pydantic request/response contracts
    │   │   └── services/
    │   │       ├── data_clients/     # retrying base client, serpapi, yfinance, quota tracker
    │   │       ├── scoring/          # normalizer, hype, fundamentals, sentiment, engine
    │   │       ├── backtest/         # forward returns + information coefficient
    │   │       ├── ingestion.py      # fetch → store raw signals + articles
    │   │       └── alerts.py         # watchlist threshold notifications
    │   ├── tests/                    # unit + integration, fully mocked network
    │   └── requirements*.txt
    ├── frontend/
    │   └── src/
    │       ├── api/                  # typed fetch client per resource
    │       ├── components/           # Layout, HistoryChart, TickerLogo
    │       └── pages/                # Dashboard, TickerDetail, SignalReport,
    │                                 # Backtests, Watchlist, Alerts, Login, Register
    └── scripts/                      # seed, daily_update, backfill_prices,
                                      # run_backtest, rescore_sentiment, show_scores

Data flow:

    SerpAPI (news) ──┐
                     ├──► data clients (retries, timeouts, quota counting)
    yfinance ────────┘                 │
                                       ▼
                          raw_signals + news_articles
                                       │  scoring engine
                                       │  (normalization, sector-relative P/E, confidence)
                                       ▼
                                    scores ──► leaderboard, charts, alerts
                                       │
                                       └──► backtest vs price_bars
                                                └──► backtest_results ──► Signal Report

The critical design decision: **raw inputs are stored separately from derived
scores**. Scoring math can be rewritten, re-run and backtested at any time
without spending another API credit.

---

## Database Schema

| Table | Purpose |
|---|---|
| `tickers` | Symbol master list with sector, needed for peer-relative math |
| `raw_signals` | One row per ticker per day: volume, sentiment, P/E, EPS growth |
| `news_articles` | Stored headlines and snippets with per-article sentiment |
| `scores` | Derived daily hype, fundamentals, gap, confidence |
| `price_bars` | Daily adjusted close per ticker |
| `backtest_results` | Persisted IC / Pearson / return splits per run |
| `quota_usage` | API call counter per provider per day |
| `users` | Accounts for watchlists and alerts |
| `watchlists` | User ↔ ticker join, unique per pair |
| `alerts` | One notification per user per ticker per day |

Every fact table carries a unique constraint on `(ticker_id, date)` (plus
user or url where relevant), which is what makes ingestion idempotent at the
database level, not just in application code.

---

## API Reference

Base URL: `/api/v1`

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | – | Create account |
| POST | `/auth/login` | – | OAuth2 password flow, returns JWT |
| GET | `/auth/me` | JWT | Current user |
| GET | `/tickers` | – | Active ticker list |
| GET | `/tickers/{id}` | – | Ticker detail |
| GET | `/tickers/{id}/score` | – | Latest score |
| GET | `/tickers/{id}/history?days=N` | – | Score history |
| GET | `/tickers/{id}/backtest?horizon=N` | – | Per-ticker backtest summary |
| GET | `/signals/leaderboard?limit=N` | – | Latest score per ticker, ranked by gap |
| POST | `/signals/live` | – | Live lookup; rate-limited per IP per minute |
| GET | `/backtest/summary` | – | Saved global backtest runs |
| GET | `/watchlist` | JWT | User's watched tickers |
| POST | `/watchlist` | JWT | Add ticker |
| DELETE | `/watchlist/{ticker_id}` | JWT | Remove ticker |
| GET | `/alerts` | JWT | User's alerts |
| POST | `/alerts/{id}/read` | JWT | Mark alert read |
| GET | `/healthz` | – | Liveness probe for uptime monitors |

Interactive docs at `/docs` when the server runs.

---

## Local Setup

### Prerequisites

- Python 3.10+
- Node 20+
- A SerpAPI key (free tier is enough to start)

### Backend

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements-dev.txt

Create `backend/.env`:

    SERPAPI_KEY=<your key from serpapi.com>
    JWT_SECRET=<any long random string>
    JWT_ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=10080
    RATE_LIMIT_LIVE_PER_MINUTE=5
    ENVIRONMENT=development

Generate a JWT secret if needed:

    python3 -c "import secrets; print(secrets.token_urlsafe(32))"

Seed the database and start the API:

    python ../scripts/seed_db.py
    uvicorn app.main:app --reload

### Frontend

    cd frontend
    npm ci
    npm run dev

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API docs | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/healthz |

---

## Daily Pipeline

    python scripts/backfill_prices.py    # once, then weekly: 2y of adjusted closes
    python scripts/daily_update.py       # ingest → score → alert (run after market close)
    python scripts/run_backtest.py       # persist 5d and 20d IC measurements

| Script | Purpose |
|---|---|
| `seed_db.py` | Insert starter tickers (idempotent) |
| `backfill_prices.py` | Fill `price_bars`, skips existing dates |
| `daily_update.py` | Full daily cycle: ingest, score, evaluate alerts |
| `run_backtest.py` | Save IC results for the Signal Report |
| `calculate_scores.py [DATE]` | Recompute scores for one date after math changes |
| `show_scores.py [DATE]` | Print the score table to the terminal |
| `rescore_sentiment.py` | Rerun the classifier over stored articles |

Schedule it (Linux cron, weekdays 16:30):

    30 16 * * 1-5 /path/to/backend/.venv/bin/python /path/to/scripts/daily_update.py >> /path/to/daily_update.log 2>&1

---

## Sentiment Classifier Upgrade

Headline sentiment defaults to a transparent word-list lexicon. Because
every article is stored at ingestion time, the classifier can be upgraded
and all history rescored with zero additional API spend:

    pip install -r requirements-ml.txt
    echo "SENTIMENT_MODEL=finbert" >> backend/.env
    python scripts/rescore_sentiment.py

This loads ProsusAI/finbert, a transformer trained on financial headlines,
rescores every stored article, rewrites daily aggregates and recomputes all
historical scores and gaps.

---

## Testing and CI

    cd backend
    python -m pytest -q     # unit + integration suites
    ruff check .            # lint

The SerpAPI client is tested against `httpx.MockTransport` and yfinance is
monkeypatched with a fake object, so the suite exercises retries, quota
counting, ingestion and scoring without a single real network call.

GitHub Actions runs on every push: backend lint + pytest on Python 3.11,
frontend `npm ci` + type-checked production build on Node 20.

---

## Docker

Requires `JWT_SECRET` and `SERPAPI_KEY` in a root `.env` file.

    docker compose up --build

| Service | URL |
|---|---|
| Frontend (nginx) | http://localhost:8080 |
| Backend | http://localhost:8000 |
| Database | Postgres 16 in the `db` service, persisted in the `pgdata` volume |

The backend container runs `python -m app.core.init_db` before startup, so
schema creation in production is explicit rather than implicit.

---

## Deployment and Monitoring

- **Backend:** Railway or Render using `backend/Dockerfile`, with managed
  Postgres. Set `DATABASE_URL`, `JWT_SECRET`, `SERPAPI_KEY`,
  `ENVIRONMENT=production`, optional `SENTRY_DSN`. Run
  `python -m app.core.init_db` once as an init command.
- **Frontend:** Netlify, Vercel or Render Static. Build `npm run build`,
  output `dist`, env var `VITE_API_URL` pointing at the deployed backend.
- **Uptime:** point any monitor (UptimeRobot, Better Stack) at `/healthz`.
- **Errors:** Sentry free tier; the SDK initializes automatically when
  `SENTRY_DSN` is set.
- **Logs:** plain text in development, one JSON object per line in
  production, including method, path, status and duration per request.

---

## Project Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Hackathon MVP: end-to-end slice, live lookup | Done |
| 1 | Data infrastructure: retrying clients, quota tracking, idempotent ingestion | Done |
| 2 | Scoring engine v2: documented math, confidence flags, backtesting | Done |
| 3 | REST API: auth, rate limiting, watchlists | Done |
| 4 | React frontend: leaderboard, charts, watchlist, alerts UI | Done |
| 5 | Hardening: tests, CI, Docker, Postgres, logging, Sentry, disclaimer | Done |
| 6 | Extensions: stored articles, swappable FinBERT classifier, public signal report | Done |

Candidate next steps: fine-tune a headline classifier on labeled data,
model transaction costs in the backtest, push alerts to email or Telegram,
evaluate TimescaleDB if price history grows large.

---

## Judging Whether the Signal Is Real

Open the Signal Report page after a few weeks of daily runs and read three
numbers: sample size, IC, and the split between positive-gap and
negative-gap forward returns.

The honest outcomes are both useful. A sustained IC above roughly 0.05 on a
large sample is a publishable result and a reason to keep building. An IC
pinned at zero means the divergence gap is a compelling visualization with
no predictive content, and knowing that before spending a year on a trading
product is exactly what the validation layer was built to tell you.

---

*Built as a research engineering project. For educational purposes only.
Not investment advice.*