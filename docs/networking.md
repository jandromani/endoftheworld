# Networking

## Goals

The node should be discoverable and useful without WAN connectivity.

## Wired LAN

The appliance uses systemd-networkd with DHCP on common Ethernet interface patterns and enables mDNS/LLMNR support.

The hostname follows:

`endworld-<profile>`

Example:

`endworld-nomad.local`

## Wi-Fi access point

If a compatible Wi-Fi adapter is present and its driver advertises AP mode, ENDWORLD can start hostapd + dnsmasq.

Default SSIDs:

- `ENDWORLD-NANO`
- `ENDWORLD-FAMILY`
- `ENDWORLD-NOMAD`

Change default passwords before use on an untrusted network.

## Captive/offline DNS

The AP DNS configuration points local names at the node, including:

- `end.world`
- `wiki.end.world`
- `ai.end.world`
- `maps.end.world`
- `apps.end.world`
- `sync.end.world`
- `git.end.world`
- `dev.end.world`
- `rag.end.world`
- `nomad.end.world`

A wildcard fallback is used for offline captive behavior.

## No AP hardware

No Wi-Fi interface or no AP support is not fatal. The node remains available over Ethernet/LAN/mDNS.

## Threat model

The current defaults target a trusted local/field network rather than hostile Internet exposure. Do not forward these service ports directly to the public Internet without an additional authentication/TLS/reverse-proxy security design.
