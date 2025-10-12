FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .
CMD ["/bin/bash"]
