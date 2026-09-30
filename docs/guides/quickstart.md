# Quickstart

> Commands below assume a Linux builder and a cloned repository.

## 1. Clone

```bash
git clone https://github.com/jandromani/endoftheworld.git
cd endoftheworld
```

## 2. Builder setup

```bash
make builder-deps
make setup
make doctor
```

## 3. Plan before downloading

```bash
make nano-plan
make family-plan
make nomad-plan
```

Plan mode resolves live sources and checks budgets without downloading the payload.

## 4. Acquire one profile

Example:

```bash
make family-acquire
```

This may download many gigabytes and freeze container images.

Partial downloads use `.part` files and are designed to resume where supported.

## 5. Prepare

```bash
make family-prepare
```

Preparation currently includes PMTiles generation and BOM generation.

## 6. Verify

```bash
make family-verify
make family-selftest
```

## 7. Local runtime test

```bash
make family-run
make family-status
```

Then open:

`http://NODE-IP:8080`

Stop with:

```bash
make family-stop
```

## 8. Build image

```bash
make family-image
```

The default result is:

`dist/endworld-family-amd64.img`

plus its SHA-256 file.

## 9. Flash

> This destroys the target device.

```bash
make family-flash DEVICE=/dev/sdX
```

Double-check the device path before running it.

## 10. Prove offline operation

Boot the target hardware, remove WAN access, then test knowledge, AI, transcription, maps and profile-specific services.

That final hardware exercise is separate from repository CI.
