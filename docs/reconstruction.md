# Reconstruct THE ARK from Zero

This document answers the “all I have is the Git repo and Internet today; how do I recreate the artifact?” question.

## Inputs

You need:

- this Git revision;
- an x86-64 Linux builder;
- Internet;
- enough local storage;
- Docker;
- the Linux image-builder dependencies.

## 1. Install dependencies

```bash
make builder-deps
make setup
make doctor
```

## 2. Choose the product contract

```bash
PROFILE=nano
```

The source of truth is:

`profiles/$PROFILE.yml`

## 3. Resolve current upstreams

```bash
python scripts/endworld.py --profile "$PROFILE" plan
```

Read the plan before downloading.

## 4. Materialize the vault

```bash
python scripts/endworld.py --profile "$PROFILE" acquire
```

The result is:

`vault/$PROFILE/`

plus its lock.

## 5. CIVILIZATION package closure

Only for CIVILIZATION:

```bash
python scripts/endworld.py --profile civilization snapshot-packages
```

## 6. Prepare derived content

```bash
python scripts/endworld.py --profile "$PROFILE" prepare
```

## 7. Verify source + vault contracts

```bash
python scripts/endworld.py --profile "$PROFILE" verify
python scripts/endworld.py --profile "$PROFILE" selftest
```

## 8. Build the raw appliance

```bash
python scripts/endworld.py --profile "$PROFILE" build-image
```

## 9. Archive together

For long-term reproducibility preserve together:

- Git commit SHA;
- profile YAML;
- frozen vault;
- lock;
- BOM;
- resulting image SHA-256;
- hardware/boot-test notes.

A Git revision without the vault is a recipe, not the food.

A vault without the Git revision is stored food without the recipe for rebuilding the kitchen.

You want both.
