install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

seed:
	python scripts/seed_benchmark.py

guard:
	python scripts/verificar_congelamento.py

.PHONY: install test seed guard
