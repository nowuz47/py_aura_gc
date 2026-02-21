.PHONY: test dashboard up down clean

test:
	@echo "Starting A/B test with Docker Compose..."
	docker-compose -f infra/docker-compose.yaml up --build

dashboard:
	@echo "Starting dashboard only..."
	docker-compose -f infra/docker-compose.yaml up dashboard

up:
	@echo "Starting all services..."
	docker-compose -f infra/docker-compose.yaml up -d

down:
	@echo "Stopping all services..."
	docker-compose -f infra/docker-compose.yaml down

clean:
	@echo "Cleaning up..."
	docker-compose -f infra/docker-compose.yaml down -v
	docker system prune -f

results:
	@mkdir -p results
