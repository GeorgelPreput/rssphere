SHELL := /bin/bash

setup:
	pyenv install --skip-existing 3.12.4
	pyenv local 3.12.4
	which python
	python --version

	poetry env use 3.12.4
	poetry install
	. .venv/bin/activate
	.venv/bin/pre-commit install

test:
	. .venv/bin/activate
	.venv/bin/pre-commit run --all-files
	poetry update
	poetry build
	poetry install --only-root
	pytest --cov=src tests/

clean:
	-@if command -v deactivate &> /dev/null; then \
		bash -c "source deactivate" || true; \
	fi
	rm -rf .venv
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
	find . -name ".mypy_cache" -type d -exec rm -rf {} +
	find . -name ".ruff_cache" -type d -exec rm -rf {} +
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.egg-info" -type d -exec rm -rf {} +
	find . -name "*.dist-info" -type d -exec rm -rf {} +
	find . -name "*.egg" -type d -exec rm -rf {} +

docs:
	mkdocs build
