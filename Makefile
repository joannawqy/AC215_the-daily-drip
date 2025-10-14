DOCKER_COMPOSE := docker compose

.PHONY: run pipeline rag down clean

run:
	@status=0; \
	$(DOCKER_COMPOSE) up --build agent || status=$$?; \
	if [ $$status -eq 130 ]; then \
		echo "docker compose interrupted by user"; \
		exit 0; \
	fi; \
	exit $$status

start:
	@status=0; \
	$(DOCKER_COMPOSE) up rag agent || status=$$?; \
	if [ $$status -eq 130 ]; then \
		echo "docker compose interrupted by user"; \
		exit 0; \
	fi; \
	exit $$status

pipeline:
	$(DOCKER_COMPOSE) up --build ingest chunk index

rag:
	@status=0; \
	$(DOCKER_COMPOSE) up --build rag || status=$$?; \
	if [ $$status -eq 130 ]; then \
		echo "docker compose interrupted by user"; \
		exit 0; \
	fi; \
	exit $$status

down:
	$(DOCKER_COMPOSE) down

clean:
	rm -rf dailydrip_rag/data/processed/* dailydrip_rag/indexes/chroma/*
