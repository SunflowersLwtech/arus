# Arus — common operations shortcuts.
#   make dev       local backend (uvicorn :8000) with .env.local
#   make test      run pytest
#   make fmt       run ruff / prettier if installed
#   make build     rebuild frontend into frontend/dist
#   make deploy    Cloud Build → Cloud Run
#   make logs      stream Cloud Run logs
#   make demo      hit /api/demo/boot on prod
#   make eval      run the 30-sec judge_evaluate.sh

PROD_URL := https://arus-1030181742799.asia-southeast1.run.app
PROJECT  := project-349f30a3-7c3e-46dd-b95
REGION   := asia-southeast1
SERVICE  := arus

.PHONY: dev test build deploy logs demo eval clean

dev:
	@echo "Arus dev server on :8000 (MCP on :8001)"
	@GOOGLE_API_KEY=$$(grep '^GOOGLE_API_KEY=' .env.local | cut -d= -f2-) \
	 GOOGLE_CLOUD_PROJECT=$(PROJECT) FIRESTORE_ENABLED=true \
	 .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

test:
	.venv/bin/python -m pytest tests/ -v

build:
	cd frontend && npm run build

deploy:
	gcloud builds submit --config=cloudbuild.yaml --region=$(REGION) --project=$(PROJECT) .

logs:
	gcloud run services logs read $(SERVICE) --region=$(REGION) --project=$(PROJECT) --limit=80

demo:
	curl -sX POST $(PROD_URL)/api/demo/boot | python3 -m json.tool

eval:
	./scripts/judge_evaluate.sh $(PROD_URL)

clean:
	rm -rf frontend/dist frontend/node_modules .pytest_cache __pycache__ backend/__pycache__
