TESTS = tests

VENV ?= .venv
ifeq ($(OS), Windows_NT)
	BIN_PATH = $(VENV)/Scripts
else
	BIN_PATH = $(VENV)/bin
endif
CODE = tests app

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: venv
venv:
	python -m venv $(VENV)
	$(BIN_PATH)/python -m pip install --upgrade pip
	$(BIN_PATH)/python -m pip install poetry
	$(BIN_PATH)/poetry install

.PHONY: test
test: ## Runs pytest
	$(BIN_PATH)/pytest -v tests

.PHONY: activate
activate: 
	$(BIN_PATH)/activate

.PHONY: lint
lint: ## Lint code
	$(BIN_PATH)/flake8 --jobs 4 --statistics --show-source $(CODE)
	$(BIN_PATH)/pylint --jobs 4 --rcfile=setup.cfg $(CODE)
	$(BIN_PATH)/mypy $(CODE)
	$(BIN_PATH)/black --skip-string-normalization --check $(CODE)

.PHONY: format
format: ## Formats all files
	$(BIN_PATH)/isort $(CODE)
	$(BIN_PATH)/black --skip-string-normalization $(CODE)
	$(BIN_PATH)/autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	$(BIN_PATH)/unify --in-place --recursive $(CODE)

.PHONY: check
check: format lint test

.PHONY: up
up:
	docker build -t fastapi-app .
	docker run --name fastapi-app -p 8000:8000 -d fastapi-app

.PHONY: docker-test
docker-test: 
	docker exec fastapi-app pytest -v tests/

.PHONY: docker-lint
docker-lint: ## Lint code
	docker exec fastapi-app flake8 --jobs 4 --statistics --show-source $(CODE)
	docker exec fastapi-app pylint --jobs 4 --rcfile=setup.cfg $(CODE)
	docker exec fastapi-app mypy $(CODE)
	docker exec fastapi-app black --skip-string-normalization --check $(CODE)

.PHONY: docker-format
docker-format: ## Format all files
	docker exec fastapi-app isort $(CODE)
	docker exec fastapi-app black --skip-string-normalization $(CODE)
	docker exec fastapi-app autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	docker exec fastapi-app unify --in-place --recursive $(CODE)

.PHONY: docker-check
docker-check: docker-format docker-lint docker-test

.PHONY: stop
stop:
	docker stop fastapi-app
	docker rm fastapi-app
	docker image rm fastapi-app

.PHONY: ci
ci:	lint test ## Lint code then run tests
