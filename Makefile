.PHONY: install test pipeline metrics eval clean demo

install:
	pip install -e .
	pip install pytest rdflib pydantic beautifulsoup4 lxml pyshacl requests

test:
	python -m pytest tests/ -v

pipeline:
	python scripts/run_parser.py
	python -m lexgraph.graph_db.ingestao

metrics:
	python scripts/measure_graph_quality.py
	python scripts/measure_retrieval_metrics.py

eval:
	python scripts/run_baseline.py --provider mock
	python scripts/run_verifier.py --input baseline_mock.jsonl

demo:
	python scripts/demo.py

clean:
	rm -rf .pytest_cache src/lexgraph/*/__pycache__
	rm -f data/interim/corpus_v1.jsonl data/graph/corpus_real.ttl
