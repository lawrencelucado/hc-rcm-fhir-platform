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
	@echo "TODO: add API, ETL, and data validation tests"
