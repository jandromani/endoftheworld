# First Boot

## Console

Current development default:

`endworld / endworld`

Change the password immediately:

```bash
passwd
```

## Portal

On the appliance the portal listens on port 80.

Try:

`http://endworld-<profile>.local/`

Examples:

- `http://endworld-nano.local/`
- `http://endworld-family.local/`
- `http://endworld-nomad.local/`
- `http://endworld-civilization.local/`

If mDNS is unavailable, use the node's LAN IP.

## Wi-Fi

If the chipset supports Linux AP mode, ENDWORLD starts the profile SSID.

Defaults are stored in:

`/etc/endworld/profile.env`

Change `ENDWORLD_WIFI_PASSWORD` before using the network in a hostile environment.

Restart networking after editing:

```bash
sudo systemctl restart endworld-network.service
```

## Check health

```bash
sudo python3 /opt/endworld/scripts/healthcheck.py --vault /srv/endworld --profile-id <profile>
```

## Verify the frozen vault

```bash
sudo python3 /opt/endworld/scripts/verify_vault.py --vault /srv/endworld --profile-id <profile>
```

## FAMILY/NOMAD/CIVILIZATION

Open the portal first. It links to enabled local services.

Do not expose Project NOMAD, Forgejo, Syncthing, Qdrant or code-server directly to the public Internet without an additional security design.
