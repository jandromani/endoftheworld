# 🏛️ THE ARK · CIVILIZATION

**4 TB · RECONSTRUCT**

CIVILIZATION takes NOMAD's “rebuild and create” workstation and adds the beginnings of dependency closure for rebuilding larger technical systems.

## What it adds

- full Europe OpenStreetMap snapshot → PMTiles;
- immutable APT dependency snapshot;
- immutable PyPI wheel snapshot;
- immutable npm cache + lock snapshot;
- FreeCAD, KiCad, OpenSCAD and Blender source preservation;
- NumPy, SciPy, SymPy, scikit-learn and JupyterLab source preservation;
- OpenCV, GDAL and QGIS source preservation;
- OpenFOAM source preservation;
- OCI Distribution registry and PyPI server source preservation;
- all NOMAD AI, developer, survival, communications and command-center capabilities.

## Storage contract

- Target: **4,000,000,000,000 bytes**
- Reserve: **700 GB**
- Acquisition headroom: **400 GB**
- Artifact acquisition ceiling: **2.9 TB**
- Root boundary: **65,536 MiB**

The large free/mutable envelope is intentional: rebuilding systems needs working storage for repositories, package extraction, indexes, datasets and generated artifacts.

## Package closure

After Internet acquisition:

```bash
make civilization-acquire
make civilization-snapshot-packages
make civilization-prepare
make civilization-verify
```

`snapshot-packages` downloads without executing package code and freezes three deterministic TARs into the normal vault lock:

- `packages/apt.snapshot.tar`
- `packages/pypi.snapshot.tar`
- `packages/npm.snapshot.tar`

The snapshots are then covered by normal SHA-256 verification and the BOM.

This is deliberately stronger than merely preserving Bandersnatch/Verdaccio source: **the dependencies themselves are materialized while the network exists.**

## AI and runtime

CIVILIZATION reuses NOMAD's lite/general/coder model switching and services: Kiwix, llama.cpp, Whisper, Syncthing, Forgejo, Qdrant, code-server and Project NOMAD.

## Hardware

This tier is intended for a workstation/server with at least 64 GB RAM and multi-terabyte SSD/NVMe storage. Larger memory and GPU acceleration improve the 30B modes but are not required by the control plane.

## Acceptance

Repository/CI completeness is distinct from physical proof. A real 4 TB payload still needs acquisition, package snapshotting, image build, flash and repeated offline hardware boots before it can be called field-proven.
