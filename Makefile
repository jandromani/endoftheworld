PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
DEVICE ?=

.PHONY: setup builder-deps doctor scout 	nano-plan nano-acquire nano-prepare nano-verify nano-selftest nano-all nano-run nano-stop nano-status nano-image nano-flash 	family-plan family-acquire family-prepare family-verify family-selftest family-all family-run family-stop family-status family-image family-flash

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

builder-deps:
	sudo bash scripts/install_builder_deps.sh

doctor:
	$(PY) scripts/endworld.py doctor

nano-plan:
	$(PY) scripts/endworld.py --profile nano plan
nano-acquire:
	$(PY) scripts/endworld.py --profile nano acquire
nano-prepare:
	$(PY) scripts/endworld.py --profile nano prepare
nano-verify:
	$(PY) scripts/endworld.py --profile nano verify
nano-selftest:
	$(PY) scripts/endworld.py --profile nano selftest
nano-all: nano-plan nano-acquire nano-prepare nano-verify nano-selftest
nano-run:
	$(PY) scripts/endworld.py --profile nano run
nano-stop:
	$(PY) scripts/endworld.py --profile nano stop
nano-status:
	$(PY) scripts/endworld.py --profile nano status
nano-image:
	$(PY) scripts/endworld.py --profile nano build-image
nano-flash:
	@test -n "$(DEVICE)" || (echo "Usage: make nano-flash DEVICE=/dev/sdX" && exit 2)
	$(PY) scripts/endworld.py --profile nano flash "$(DEVICE)"

family-plan:
	$(PY) scripts/endworld.py --profile family plan
family-acquire:
	$(PY) scripts/endworld.py --profile family acquire
family-prepare:
	$(PY) scripts/endworld.py --profile family prepare
family-verify:
	$(PY) scripts/endworld.py --profile family verify
family-selftest:
	$(PY) scripts/endworld.py --profile family selftest
family-all: family-plan family-acquire family-prepare family-verify family-selftest
family-run:
	$(PY) scripts/endworld.py --profile family run
family-stop:
	$(PY) scripts/endworld.py --profile family stop
family-status:
	$(PY) scripts/endworld.py --profile family status
family-image:
	$(PY) scripts/endworld.py --profile family build-image
family-flash:
	@test -n "$(DEVICE)" || (echo "Usage: make family-flash DEVICE=/dev/sdX" && exit 2)
	$(PY) scripts/endworld.py --profile family flash "$(DEVICE)"

scout:
	$(PY) scripts/scout.py
