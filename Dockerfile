FROM python:3.12-slim AS builder

# Install Poetry
RUN pip install --no-cache-dir poetry==1.3.2

# Set environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN --mount=type=cache,target=/tmp/poetry_cache \
    poetry install --only main --no-root

# Final runtime stage
FROM python:3.12-slim AS runtime

# Set up virtual environment
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Add a non-root user for security
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
WORKDIR /app
COPY app ./app

# Set permissions and switch to non-root user
RUN chown -R appuser:appgroup /app
USER appuser
RUN ls
# Default command to run your main.py file
CMD ["python", "-m", "app.main"]
