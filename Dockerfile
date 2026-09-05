# Multi-stage build for Mew Assistant
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code (includes templates and static)
COPY ./app ./app
COPY init-oauth-db.py .
COPY ./scripts ./scripts

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Run migrations then start the application. create_all() (in the app's own
# startup event) only ever creates missing tables, never alters an existing
# one's columns - migrate_three_persona_scheduling.py's LATE_COLUMNS is the
# only thing that adds a column to a table that already exists in
# production, so it has to run before the app does, on every boot, not just
# be a script someone remembers to SSH in and run by hand (twice now, this
# was the actual cause of a "new column" deploy silently 500ing in prod).
# --skip-seed keeps this boot-time step to schema only.
CMD python scripts/migrate_three_persona_scheduling.py --skip-seed && python init-oauth-db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000
