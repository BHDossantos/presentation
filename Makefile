.PHONY: install test lint examples preview

install:
	pip install -e ".[dev,qa]"

test:
	pytest -q

lint:
	ruff check .

examples:
	deckgen batch examples/batch.yaml -o out/batch

preview:
	deckgen outline examples/energy-efficient-buildings.md -o out -f pptx,html,pdf,json
	deckgen thumbnails out/energy-efficient-buildings.pptx -o out/energy-thumbs
