PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: setup nano-plan nano-acquire nano-verify nano-run nano-stop nano-status

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

nano-plan:
	$(PY) scripts/build_nano.py plan

nano-acquire:
	$(PY) scripts/build_nano.py acquire

nano-verify:
	$(PY) scripts/verify_vault.py --vault vault/nano

nano-run:
	bash runtime/start-nano.sh

nano-stop:
	bash runtime/stop-nano.sh

nano-status:
	@echo "Vault:"
	@du -sh vault/nano 2>/dev/null || echo "  not acquired"
	@echo "Lock:"
	@test -f vault/nano/lock/nano.lock.json && $(PY) -c 'import json;d=json.load(open("vault/nano/lock/nano.lock.json"));print("  payload:",round(d["payload_bytes"]/1e9,2),"GB");print("  generated:",d["generated_at"])' || echo "  no lock"
