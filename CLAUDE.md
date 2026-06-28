# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Frontend (SvelteKit)
- **Install dependencies:** `npm install --force`
- **Run development server:** `npm run dev` (Starts frontend and Vite dev server)
- **Build for production:** `npm run build`
- **Preview production build:** `npm run preview`
- **Type check:** `npm run check` (Runs `svelte-check`)
- **Lint code:** `npm run lint:frontend` (Runs ESLint)
- **Format code:** `npm run format` (Runs Prettier on JS/TS/Svelte/CSS/MD/HTML/JSON)
- **Run unit tests:** `npm run test:frontend` (Runs Vitest)

### Backend (Python/FastAPI)
- **Development Server:** Start the FastAPI backend with `./backend/dev.sh`. Alternatively, run `python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload`.
- **Lint backend:** `npm run lint:backend` (Runs `pylint backend/`)
- **Format backend:** `npm run format:backend` (Runs `ruff format` on the backend)

### Full Stack
- **Run all linters:** `npm run lint` (Runs frontend, types, and backend linting)
- **Docker Compose (Full Stack):** `docker-compose up -d --build` or `make startAndBuild`

## High-Level Architecture

Open WebUI is a self-hosted AI platform containing a frontend (SvelteKit) and a backend (Python/FastAPI). It interfaces seamlessly with LLMs through Ollama, OpenAI-compatible APIs, and HuggingFace, acting as a user-friendly deployment solution with built-in RAG capabilities.

### Frontend (`src/`)
- **Framework:** Built with SvelteKit (`src/lib`, `src/routes`), Tailwind CSS, and Vite.
- **`src/lib/apis/`**: Contains fetch wrappers to communicate with the Python backend API (e.g., `chats`, `models`, `users`, `openai`, `ollama`).
- **`src/lib/components/`**: Modular Svelte UI components (e.g., `admin`, `chat`, `common`, `layout`). 
- **`src/lib/stores/`**: Svelte stores for application state (config, user, themes, active models).
- **Styling:** Controlled through `tailwind.config.js` and `app.css`.

### Backend (`backend/`)
- **Framework:** Built with FastAPI (`backend/open_webui/main.py`), utilizing Uvicorn as the ASGI server.
- **`open_webui/main.py`:** The primary entry point. Initializes FastAPI, connects to the database, configures CORS, and registers all routers.
- **`open_webui/routers/`**: Contains API route definitions organized by domain (`chats.py`, `models.py`, `users.py`, `auths.py`, `ollama.py`, `retrieval.py`, etc.). These handle the REST endpoints called by the frontend.
- **`open_webui/models/`**: Defines SQLAlchemy ORM models, Pydantic schemas for request/response validation, and database operations.
- **`open_webui/internal/`**: Core internal logic including database connection setup (`db.py`) and configuration management (`config.py`).
- **`open_webui/utils/`**: Helper functions, middleware for request processing, payload manipulation, background tasks, and integrations (e.g., OAuth, AuthLib).
- **Database:** Uses SQLAlchemy with async support (often SQLite by default via `aiosqlite`, with migrations managed by Alembic).
- **Migrations:** Handled via Alembic (`backend/open_webui/migrations/` and `alembic.ini`).

### Key Flows
- **Authentication:** JWT-based or OAuth. Routes are protected via FastAPI dependency injection checking the user role.
- **Chat/Inference:** Handled in specific routers like `chats.py` and `ollama.py`. The backend proxies and standardizes requests to the underlying LLM runners (Ollama, OpenAI API) and handles streaming responses via WebSockets or Server-Sent Events (SSE).
- **Tools/Functions:** Supports executing code on the server or interacting with external APIs, dynamically injected into the LLM context.
- **RAG (Retrieval-Augmented Generation):** Integrated into the inference pipeline, allowing document uploads, parsing, and vector similarity search.