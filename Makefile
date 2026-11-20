#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = seminal
PYTHON_VERSION = 3.12
PYTHON_INTERPRETER = python
CONDA_ENV = conda_312
VENV_DIR = seminal_venv

#################################################################################
# ENVIRONMENT                                                                   #
#################################################################################

## Create venv on top of the active conda env (run `conda activate $(CONDA_ENV)` first)
venv:
	$(PYTHON_INTERPRETER) -m venv $(VENV_DIR)
	@echo ">>> Activate with: source $(VENV_DIR)/bin/activate"

## Install the package in editable mode with dev and data extras
install:
	$(PYTHON_INTERPRETER) -m pip install --upgrade pip
	$(PYTHON_INTERPRETER) -m pip install -e ".[dev,data]"

#################################################################################
# PROJECT COMMANDS                                                              #
#################################################################################

## Run the test suite
test:
	$(PYTHON_INTERPRETER) -m pytest -v

## Run the test suite with a coverage report
coverage:
	$(PYTHON_INTERPRETER) -m pytest tests/ --cov=src/seminal --cov-report=term-missing

## Build the Sphinx docs into docs/_build/html
docs:
	$(MAKE) -C docs html

## Download the Tradewell 2022 Dataverse file into data/raw
data_gen:
	$(PYTHON_INTERPRETER) data_gen.py --csv

## Harmonize sites into data/processed/tradewell_2022.parquet
preprocess:
	$(PYTHON_INTERPRETER) preprocessing.py --csv

## Build sdist and wheel into dist/
build:
	$(PYTHON_INTERPRETER) -m pip install --upgrade build
	$(PYTHON_INTERPRETER) -m build

## Remove build artifacts and caches
clean:
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache docs/_build
	find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: venv install test coverage docs data_gen preprocess build clean help

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

## Show this help
help:
	@echo "Available targets:"
	@awk '/^## /{desc=substr($$0,4); getline; split($$0,t,":"); printf "  \033[36m%-12s\033[0m %s\n", t[1], desc}' $(MAKEFILE_LIST)
