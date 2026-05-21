.PHONY: help up down logs build rebuild ps shell-backend shell-db reset secrets test lint

help:
	@echo "Cibles disponibles :"
	@echo "  make up          - Lance la stack (build + start)"
	@echo "  make down        - Arrête la stack"
	@echo "  make logs        - Tail logs en direct"
	@echo "  make rebuild     - Rebuild complet sans cache"
	@echo "  make ps          - Liste containers"
	@echo "  make shell-backend - Shell dans le container backend"
	@echo "  make shell-db    - psql dans postgres"
	@echo "  make reset       - DROP DB + redémarre (DESTRUCTIF)"
	@echo "  make secrets     - Génère JWT_SECRET et MASTER_ENCRYPTION_KEY"
	@echo "  make test        - Lance les tests pytest"

up:
	docker compose up -d --build
	@echo "✅ Frontend → http://localhost:8080"
	@echo "✅ API     → http://localhost:8080/api"
	@echo "✅ Docs    → http://localhost:8080/docs"

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

build:
	docker compose build

rebuild:
	docker compose build --no-cache

ps:
	docker compose ps

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U $${POSTGRES_USER:-simplifia} -d $${POSTGRES_DB:-simplifia}

reset:
	docker compose down -v
	docker compose up -d --build

secrets:
	@echo "JWT_SECRET=$$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
	@echo "MASTER_ENCRYPTION_KEY=$$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

test:
	docker compose exec backend pytest -v

lint:
	docker compose exec backend ruff check app/
