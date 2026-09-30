PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
DEVICE ?=

.PHONY: setup builder-deps doctor scout 	nano-plan nano-acquire nano-prepare nano-verify nano-selftest nano-all nano-run nano-stop nano-status nano-image nano-flash 	family-plan family-acquire family-prepare family-verify family-selftest family-all family-run family-stop family-status family-image family-flash 	nomad-plan nomad-acquire nomad-prepare nomad-verify nomad-selftest nomad-all nomad-run nomad-stop nomad-status nomad-image nomad-flash nomad-ai-lite nomad-ai-general nomad-ai-coder 	civilization-plan civilization-acquire civilization-snapshot-packages civilization-prepare civilization-verify civilization-selftest civilization-all civilization-run civilization-stop civilization-status civilization-image civilization-flash civilization-ai-lite civilization-ai-general civilization-ai-coder

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

nomad-plan:
	$(PY) scripts/endworld.py --profile nomad plan
nomad-acquire:
	$(PY) scripts/endworld.py --profile nomad acquire
nomad-prepare:
	$(PY) scripts/endworld.py --profile nomad prepare
nomad-verify:
	$(PY) scripts/endworld.py --profile nomad verify
nomad-selftest:
	$(PY) scripts/endworld.py --profile nomad selftest
nomad-all: nomad-plan nomad-acquire nomad-prepare nomad-verify nomad-selftest
nomad-run:
	$(PY) scripts/endworld.py --profile nomad run
nomad-stop:
	$(PY) scripts/endworld.py --profile nomad stop
nomad-status:
	$(PY) scripts/endworld.py --profile nomad status
nomad-image:
	$(PY) scripts/endworld.py --profile nomad build-image
nomad-flash:
	@test -n "$(DEVICE)" || (echo "Usage: make nomad-flash DEVICE=/dev/sdX" && exit 2)
	$(PY) scripts/endworld.py --profile nomad flash "$(DEVICE)"
nomad-ai-lite:
	$(PY) scripts/endworld.py --profile nomad ai-mode lite
nomad-ai-general:
	$(PY) scripts/endworld.py --profile nomad ai-mode general
nomad-ai-coder:
	$(PY) scripts/endworld.py --profile nomad ai-mode coder

civilization-plan:
	$(PY) scripts/endworld.py --profile civilization plan
civilization-acquire:
	$(PY) scripts/endworld.py --profile civilization acquire
civilization-snapshot-packages:
	$(PY) scripts/endworld.py --profile civilization snapshot-packages
civilization-prepare:
	$(PY) scripts/endworld.py --profile civilization prepare
civilization-verify:
	$(PY) scripts/endworld.py --profile civilization verify
civilization-selftest:
	$(PY) scripts/endworld.py --profile civilization selftest
civilization-all: civilization-plan civilization-acquire civilization-snapshot-packages civilization-prepare civilization-verify civilization-selftest
civilization-run:
	$(PY) scripts/endworld.py --profile civilization run
civilization-stop:
	$(PY) scripts/endworld.py --profile civilization stop
civilization-status:
	$(PY) scripts/endworld.py --profile civilization status
civilization-image:
	$(PY) scripts/endworld.py --profile civilization build-image
civilization-flash:
	@test -n "$(DEVICE)" || (echo "Usage: make civilization-flash DEVICE=/dev/sdX" && exit 2)
	$(PY) scripts/endworld.py --profile civilization flash "$(DEVICE)"
civilization-ai-lite:
	$(PY) scripts/endworld.py --profile civilization ai-mode lite
civilization-ai-general:
	$(PY) scripts/endworld.py --profile civilization ai-mode general
civilization-ai-coder:
	$(PY) scripts/endworld.py --profile civilization ai-mode coder
