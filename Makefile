.PHONY: validate validate-spec test demo

PYTHON ?= python3
export PYTHONPATH := src

validate: validate-spec test
	$(PYTHON) -m compileall -q src tests scripts

validate-spec:
	$(PYTHON) scripts/validate_spec.py

test:
	$(PYTHON) -m unittest discover -s tests -v

demo:
	$(PYTHON) -m iaap_guard.cli scan fixtures/good/product-contract.yaml --repository iaap-guard-demo --revision 0000000000000000000000000000000000000000
