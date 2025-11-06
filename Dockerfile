# syntax=docker/dockerfile:1

FROM python:3.13-slim

# Application environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

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
