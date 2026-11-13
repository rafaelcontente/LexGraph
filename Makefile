.PHONY: install test pipeline metrics clean

install:
	pip install -e .
	pip install pytest rdflib pydantic beautifulsoup4 lxml pyshacl

test:
	python -m pytest tests/ -v

# Corre o pipeline completo de dados
pipeline:
	python scripts/run_parser.py
	python -m lexgraph.graph_db.ingestao

# Corre as métricas de qualidade e recuperação
metrics:
	python scripts/measure_graph_quality.py
	python scripts/measure_retrieval_metrics.py

# Corre o baseline e o verificador (Mock)
eval:
	python scripts/run_baseline.py --provider mock
	python scripts/run_verifier.py --input baseline_mock.jsonl

clean:
	rm -rf .pytest_cache src/lexgraph/*/__pycache__
	rm -f data/interim/corpus_v1.jsonl data/graph/corpus_real.ttl
