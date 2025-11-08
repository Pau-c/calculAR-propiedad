# syntax=docker/dockerfile:1

FROM python:3.13-slim

# Application environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app


# --- DATADOG APM TRACER INJECTION START ---
# 1. Set environment variables for the Datadog Instrumentation Libraries
# DD_NO_AGENT_INSTALL=true ensures only the APM libraries are installed, not the full agent.
# ENV DD_APM_INSTRUMENTATION_LIBRARIES="python:3"
ENV DD_APM_INSTRUMENTATION_LIBRARIES="java:1,python:3,js:5,php:1,dotnet:3,ruby:2" \
    DD_APM_INSTRUMENTATION_ENABLED="docker" \
    DD_NO_AGENT_INSTALL="true"

# 2. Install curl and run the Datadog script to inject the APM tracing libraries.
# This runs everything in one layer: update, install curl, run the script, then cleanup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && bash -c "$(curl -L https://install.datadoghq.com/scripts/install_script_agent7.sh)" \
    && apt-get remove --purge -y curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# --- DATADOG APM TRACER INJECTION END ---

# Install uv 
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files  (so Docker can cache layers)
COPY pyproject.toml uv.lock ./

# Create virtualenv inside image
RUN uv sync --python /usr/local/bin/python3.13 --frozen --no-cache

# Copy the rest of the app code
COPY . .

EXPOSE 8000

# the Datadog tracer will be auto-injected when the app runs.
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
