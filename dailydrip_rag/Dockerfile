FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git curl && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin:${PATH}"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV UV_HTTP_TIMEOUT=300

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY data ./data

ENV UV_PROJECT_ENVIRONMENT=/opt/rag-venv
RUN uv venv ${UV_PROJECT_ENVIRONMENT} && \
    . ${UV_PROJECT_ENVIRONMENT}/bin/activate && \
    uv pip install --no-cache-dir --editable .
ENV PATH="/opt/rag-venv/bin:${PATH}"

CMD ["/bin/bash"]
