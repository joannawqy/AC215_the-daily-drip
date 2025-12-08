DOCKER_COMPOSE := docker compose

.PHONY: run start rag down clean build-runtime

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
	$(DOCKER_COMPOSE) up rag agent frontend || status=$$?; \
	if [ $$status -eq 130 ]; then \
		echo "docker compose interrupted by user"; \
		exit 0; \
	fi; \
	exit $$status

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

# Build all runtime images (rag, agent, and frontend)
build-runtime:
	@echo "Building runtime images..."
	$(DOCKER_COMPOSE) build rag agent frontend

