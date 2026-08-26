.PHONY: install test run

install:
	@echo "Installing package in editable mode with dev dependencies..."
	pip install -e .[dev]

test:
	@echo "Running pytest..."
	pytest -q

run:
	@echo "Running the Hello World program..."
	python -m hello
