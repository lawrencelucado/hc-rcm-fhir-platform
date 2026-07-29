up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

seed:
	@echo "TODO: load sample data into raw storage and database"

run-etl:
	@echo "TODO: implement ETL runner"

dbt:
	@echo "TODO: implement dbt build flow"

export-fhir:
	@echo "TODO: implement FHIR export"

test:
	python scripts/validate_repository.py
	python -m unittest discover -s tests -p "test_safe_*.py" -v

test-live-mirth:
	@echo "Live Mirth testing is intentionally gated. See tests/test_mirth_integration.py."
	python tests/test_mirth_integration.py

test-live-smart:
	@echo "Live SMART testing is intentionally gated. See tests/test_smart_gateway.py."
	python tests/test_smart_gateway.py
