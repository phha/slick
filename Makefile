#
# vim:ft=make
# Makefile
#
.DEFAULT_GOAL := help
.PHONY: test help install showdeps isort lint format check build


help:  ## these help instructions
	@sed -rn 's/^([a-zA-Z_-]+):.*?## (.*)$$/"\1" "\2"/p' < $(MAKEFILE_LIST)|xargs printf "make %-20s# %s\n"

install: ## Run `poetry install`
	@poetry install

showdeps: ## run poetry to show deps
	@echo "CURRENT:"
	@poetry show --tree
	@echo
	@echo "LATEST:"
	@poetry show --latest

isort: ## Runs isort
	@poetry run isort .

lint: ## Runs flake8
	@poetry run pflake8

format: ## Formats you code with Black
	@poetry run black . --target-version=py36

test: ## run pytest with coverage
	@poetry run pytest --cov

check: isort format lint test ## Perform sorting, formatting, linting and testing

build: check ## run `poetry build` to build source distribution and wheel
	@poetry build