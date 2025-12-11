DOCKER_COMPOSE := docker compose -f deployment/docker-compose.yml

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
	$(DOCKER_COMPOSE) up --build app || status=$$?; \
	if [ $$status -eq 130 ]; then \
		echo "docker compose interrupted by user"; \
		exit 0; \
	fi; \
	exit $$status

rag:
	@echo "RAG is now part of the monolithic app. Run 'make start' to start everything."

down:
	$(DOCKER_COMPOSE) down

clean:
	rm -rf dailydrip_rag/data/processed/* dailydrip_rag/indexes/chroma/*

# Build monolith image
build-runtime:
	@echo "Building monolithic image..."
	$(DOCKER_COMPOSE) build app
