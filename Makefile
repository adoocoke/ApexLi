test:
	pytest -v

test-cov:
	pytest --cov=eaagent --cov-report=term-missing

lint:
	ruff check eaagent tests

format:
	ruff format eaagent tests
