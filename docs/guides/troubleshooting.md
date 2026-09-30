# Troubleshooting

## “Frozen lock missing”

Run acquisition for the selected profile.

```bash
make <profile>-acquire
```

## “No PMTiles map found”

Run preparation.

```bash
make <profile>-prepare
```

Planetiler requires Java and substantial temporary disk space.

## Docker daemon unavailable

Check:

```bash
docker info
systemctl status docker
```

On the appliance, the `endworld` user is added to the Docker group.

## Wi-Fi AP does not start

The runtime only enables AP mode when a wireless interface exists and the driver advertises AP support.

The supported fallback is Ethernet/LAN + mDNS.

Check:

```bash
iw dev
iw list
rfkill
```

## Kiwix starts but library is empty

Verify ZIM files exist under:

`/srv/endworld/knowledge/zim`

and are present in the selected profile lock.

## AI does not start

Check:

- model record exists in lock;
- GGUF exists under `ai/models`;
- frozen llama.cpp container exists;
- enough RAM is available.

NOMAD users can fall back to:

```bash
make nomad-ai-lite
```

## AI is extremely slow

CPU inference can be slow on large models. Use a smaller mode, reduce context or use supported GPU acceleration.

## Whisper fails on large audio

The portal enforces a maximum upload body. Split very large recordings or use the underlying local service directly.

## Forgejo or Syncthing resets

Confirm `state/forgejo` and `state/syncthing` are persistent and writable.

## Qdrant data disappears

Confirm `state/qdrant` is mounted into the container and was not removed with the vault.

## Project NOMAD does not become healthy

Check MySQL first. The ENDWORLD launcher waits for MySQL before starting admin.

Inspect:

```bash
docker logs endworld-nomad-mysql
docker logs endworld-nomad-redis
docker logs endworld-nomad-admin
```

## Source planning fails

Upstream naming can change. Run the failing URL/index manually, compare current filenames with the profile regex and update the manifest deliberately.

Do not weaken a required source to optional merely to make CI green without understanding the impact.
