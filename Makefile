.PHONY: validate

PYTHON ?= python3

validate:
	$(PYTHON) scripts/validate_spec.py
