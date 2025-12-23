# IntelliQuery-AI

Voxalize (IntelliQuery-AI) is a voice-driven conversational analytics platform that lets analysts, operators, and business teams query SQL, MongoDB, and spreadsheet-style datasets using natural language. The backend is built around FastAPI services with LangChain-powered LLM agents that synthesize questions, route them to the right datastore, and return structured answers along with executive summaries and chart-ready aggregates. All query execution is read-only, with SQLAlchemy and bespoke guards ensuring schema integrity.

## Literature Overview

Recent progress across both commercial tooling and academic research motivates IntelliQuery-AI:

- **Commercial conversational BI.** Products such as BlazeSQL, DataGPT, and Google Looker Conversational Analytics prove that NL-powered querying lowers the entry barrier to data exploration. Their focus remains tightly coupled to SQL warehouses, they are closed-source, and they rarely expose extensibility hooks for hybrid backends. Enterprises that juggle relational, document, and ad-hoc spreadsheet data still need parallel workflows.
- **Text-to-SQL research.** Benchmarks like WikiSQL, Spider, and BIRD have established a rigorous evaluation regime for mapping natural language to SQL. Transformer-class models (GPT, LLaMA, Mistral) consistently push state of the art in compositional generalization, prompting robust query planners that handle joins, nested filters, and schema grounding. Yet these contributions stop at SQL generation and do not tackle execution safety, post-processing, or result narration.
- **Agent frameworks and tool orchestration.** Platforms such as LangChain enable LLM agents to call databases, APIs, and analytical runtimes, but most reference implementations target SQL-only workloads. Unified handling of SQL, Pandas (Excel), and MongoDB remains underexplored, especially when coupled with no-code data manipulation assurances and fine-grained governance.

These gaps call for a research-oriented, extensible system that blends multi-backend query planning, read-only enforcement, and narrated insight delivery. IntelliQuery-AI addresses that need by pairing dataset-aware agent routing with secure execution adapters and LLM-driven summarization.

## Architecture

- **FastAPI service (`backend/app.py`).** Boots the API surface, wires CORS from environment variables, registers auth routes, and runs Mongo connectivity + index checks during startup so failures surface immediately.
- **Authentication module (`backend/auth/*`).** Provides user registration/login/logout flows, PBKDF2 password hashing, JWT creation/verification, and stateless cookie middleware that injects the current user into each request.
- **Persistence utilities (`backend/utils/db.py`).** Centralizes MongoDB client creation, database selection, and readiness probing for the auth service.
- **Data assets (`backend/data/*.csv`).** Sample corpora for SQL, Mongo, and Pandas prompt tuning plus offline experimentation.
- **Research notebooks (`backend/notebooks/*.ipynb`).** Contain fine-tuning and evaluation workflows for Mongo and Pandas text-to-query adapters.
- **Frontend stub (`src/`).** React + Tailwind Vite app currently hosting a placeholder view, ready to embed the future conversational workspace.

## Core Capabilities

- User onboarding with username/email/password validation, hashed credentials, and duplicate checks backed by Mongo unique indexes.
- Session management via signed JWT cookies, configurable SameSite/Secure flags, and middleware-driven request context injection.
- Environment-driven configuration for auth secrets, token TTLs, Mongo URIs, and CORS origin allow-lists.
- Database readiness probing at startup so dependent services fail fast when Mongo is unavailable.
- Research collateral (datasets + notebooks) to iterate on text-to-SQL/Mongo/Pandas generation pipelines before wiring them into the API.

## Tech Stack

- **Backend Runtime:** FastAPI + Uvicorn (async ASGI) with Starlette middleware for cookies/CORS.
- **Persistence:** MongoDB via PyMongo, with utility helpers for clients and unique index enforcement.
- **Data/ML Libraries:** LangChain, Groq SDK, Pandas, SQLAlchemy (for upcoming SQL routing), Plotly/Matplotlib for server-side visualization.
- **Security/Identity:** Passlib (PBKDF2 hashing), PyJWT for token issuance, custom cookie policy helpers.
- **Tooling:** python-dotenv for configuration, pytest-ready structure, and notebooks for experimentation.

## Tools and Technology Used

- **Frontend:** React 19 + Vite with Tailwind CSS v4 for rapid prototyping (currently a scaffolded landing view ready for future components).
- **Backend:** FastAPI application with modular auth routes, CORS middleware, and environment-driven startup hooks. Uvicorn powers local development.
- **Security:** Passlib PBKDF2 hashing, JWT signing via PyJWT, HTTP-only cookies with configurable SameSite/Secure policies, and Mongo unique indexes.
- **AI & Analytics:** LangChain + Groq client libraries (wired via requirements) alongside Pandas, SQLAlchemy, Plotly, and Matplotlib for data prep and visualization experiments in notebooks.
- **Data Stores:** MongoDB is the operational metadata store today; SQL engines (via SQLAlchemy) and Pandas-backed CSV/Excel files sit in `backend/data` for upcoming multi-backend routing.
