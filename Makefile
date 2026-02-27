PYTHON  = python
UVICORN = uvicorn
PYTEST  = python -m pytest

.PHONY: serve test import-graph

serve:
	PYTHONPATH=src $(UVICORN) backend.main:app --host 0.0.0.0 --port 8000

test:
	$(PYTEST) tests/ -v

import-graph:
	PYTHONPATH=src $(PYTHON) src/graph/eci_neo4j_importer.py
