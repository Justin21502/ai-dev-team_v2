.PHONY: install test run

install:
	@echo "Installing package in editable mode with dev dependencies..."
	cd workspace && pip install -e .[dev]

test:
	@echo "Running pytest..."
	cd workspace && pytest -q

run:
	@echo "Running the Hello World program..."
	cd workspace && python -m hello
