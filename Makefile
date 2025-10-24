.PHONY: help build up down logs test clean deploy backup restore

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start services
	docker-compose up -d

down: ## Stop services
	docker-compose down

logs: ## View logs
	docker-compose logs -f

test: ## Run tests
	docker-compose exec api pytest tests/ -v

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

deploy: ## Deploy to Kubernetes
	./scripts/deploy.sh

backup: ## Backup database
	./scripts/backup.sh

restore: ## Restore database (usage: make restore FILE=backup.sql.gz)
	./scripts/restore.sh $(FILE)

shell: ## Open shell in API container
	docker-compose exec api /bin/bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec db psql -U postgres meter_readings

migrations: ## Create new migration
	docker-compose exec api alembic revision --autogenerate -m "$(message)"

migrate: ## Run migrations
	docker-compose exec api alembic upgrade head

downgrade: ## Downgrade migration
	docker-compose exec api alembic downgrade -1

scale: ## Scale API replicas (usage: make scale REPLICAS=5)
	kubectl scale deployment/api-deployment --replicas=$(REPLICAS) -n meter-reading

status: ## Check deployment status
	kubectl get all -n meter-reading