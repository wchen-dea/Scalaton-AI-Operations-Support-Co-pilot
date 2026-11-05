.DEFAULT_GOAL := help

TARGET ?= dev
PROFILE ?= $(TARGET)
APP_NAME ?= scalaton-$(TARGET)
APP_SERVICE_PRINCIPAL ?=
APP_PERMISSION_LEVEL ?= CAN_USE
TARGET_FILE ?= targets/$(TARGET).yml

DBX := databricks --profile $(PROFILE)
DBX_BUNDLE := $(DBX) bundle --target $(TARGET)
DBX_APP := $(DBX) apps

.PHONY: help install build wheel check-env validate deploy grant-app-permissions start stop logs

help: ## Show local development targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-24s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install frontend dependencies
	cd frontend && npm ci

build: ## Build the frontend for the Databricks App
	cd frontend && npm run build

wheel: build ## Build a wheel containing the backend and frontend
	rm -rf backend/app/static dist
	mkdir -p backend/app/static dist
	cp -R frontend/dist/. backend/app/static/
	uv build backend --out-dir dist

check-env: ## Check that the selected target configuration exists
	@test -f "$(TARGET_FILE)" || (echo "Target configuration not found: $(TARGET_FILE)" >&2; exit 1)

validate: check-env ## Validate the selected Databricks Asset Bundle target
	$(DBX_BUNDLE) validate --strict

deploy: wheel validate ## Build the wheel and deploy the selected target app
	$(DBX_BUNDLE) deploy

grant-app-permissions: check-env ## Grant APP_SERVICE_PRINCIPAL access to the selected app
	@test -n "$(APP_SERVICE_PRINCIPAL)" || (echo "APP_SERVICE_PRINCIPAL is required" >&2; exit 1)
	$(DBX_APP) update-permissions $(APP_NAME) --json '{"access_control_list":[{"service_principal_name":"$(APP_SERVICE_PRINCIPAL)","permission_level":"$(APP_PERMISSION_LEVEL)"}]}'

start: check-env ## Start the selected target app
	$(DBX_APP) start $(APP_NAME) --target $(TARGET)

stop: check-env ## Stop the selected target app
	$(DBX_APP) stop $(APP_NAME) --target $(TARGET)

logs: check-env ## Show logs for the selected target app
	$(DBX_APP) logs $(APP_NAME) --target $(TARGET)