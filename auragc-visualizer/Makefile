.PHONY: test dashboard up down clean build-wheel

build-wheel:
	@echo "Building auragc-core wheel..."
	@cd ../auragc-core && ./build_wheel.sh

test: build-wheel
	@echo "Starting A/B test with Docker Compose..."
	@if command -v docker-compose > /dev/null; then \
		docker-compose -f infra/docker-compose.yaml up --build; \
	else \
		docker compose -f infra/docker-compose.yaml up --build; \
	fi

dashboard:
	@echo "Starting dashboard only..."
	docker-compose -f infra/docker-compose.yaml up dashboard

up: build-wheel
	@echo "Starting all services..."
	@if command -v docker-compose > /dev/null; then \
		docker-compose -f infra/docker-compose.yaml up -d; \
	else \
		docker compose -f infra/docker-compose.yaml up -d; \
	fi

down:
	@echo "Stopping all services..."
	@if command -v docker-compose > /dev/null; then \
		docker-compose -f infra/docker-compose.yaml down; \
	else \
		docker compose -f infra/docker-compose.yaml down; \
	fi

clean:
	@echo "Cleaning up..."
	@if command -v docker-compose > /dev/null; then \
		docker-compose -f infra/docker-compose.yaml down -v; \
	else \
		docker compose -f infra/docker-compose.yaml down -v; \
	fi
	@docker system prune -f
	@rm -rf ../wheels/*.whl 2>/dev/null || true

results:
	@mkdir -p results
