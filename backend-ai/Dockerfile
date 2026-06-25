FROM python:3.12.8-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd --create-home --shell /usr/sbin/nologin codepulse \
    && mkdir -p /tmp/codepulse /tmp/codepulse-reports \
    && chown -R codepulse:codepulse /app /tmp/codepulse /tmp/codepulse-reports \
    && chmod -R a-w /app \
    && chmod -R u+w /tmp/codepulse /tmp/codepulse-reports
USER codepulse
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health >/dev/null || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
