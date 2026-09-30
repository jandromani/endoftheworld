PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
DEVICE ?=

.PHONY: setup builder-deps doctor nano-plan nano-acquire nano-prepare nano-verify nano-all nano-run nano-stop nano-status nano-image nano-flash scout

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

builder-deps:
	sudo bash scripts/install_builder_deps.sh

doctor:
	$(PY) scripts/endworld.py doctor

nano-plan:
	$(PY) scripts/endworld.py plan

nano-acquire:
	$(PY) scripts/endworld.py acquire

nano-prepare:
	$(PY) scripts/endworld.py prepare

nano-verify:
	$(PY) scripts/endworld.py verify

nano-all: nano-plan nano-acquire nano-prepare nano-verify

nano-run:
	$(PY) scripts/endworld.py run

nano-stop:
	$(PY) scripts/endworld.py stop

nano-status:
	$(PY) scripts/endworld.py status

nano-image:
	$(PY) scripts/endworld.py build-image

nano-flash:
	@test -n "$(DEVICE)" || (echo "Usage: make nano-flash DEVICE=/dev/sdX" && exit 2)
	$(PY) scripts/endworld.py flash "$(DEVICE)"

scout:
	$(PY) scripts/scout.py
