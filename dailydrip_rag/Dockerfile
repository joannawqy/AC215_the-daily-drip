FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git curl && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
RUN /root/.cargo/bin/uv pip install -e .
CMD ["/bin/bash"]