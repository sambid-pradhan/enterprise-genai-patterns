FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates nodejs npm gh bubblewrap \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

RUN npm install -g @openai/codex || true

COPY app ./app
COPY prompts ./prompts
COPY sample_target_repo ./sample_target_repo
COPY worker ./worker

RUN chmod +x /workspace/worker/entrypoint.sh

EXPOSE 8000

CMD ["/workspace/worker/entrypoint.sh"]
