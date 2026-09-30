#!/usr/bin/env bash
set -euo pipefail
ACTION="${1:-start}"
RUN=/run/endworld
ETC=/etc/endworld
mkdir -p "$RUN"
[[ -f "$ETC/profile.env" ]] && source "$ETC/profile.env"
SSID="${ENDWORLD_WIFI_SSID:-ENDWORLD-NANO}"
PASS="${ENDWORLD_WIFI_PASSWORD:-endworld-nano}"
ADDR="${ENDWORLD_WIFI_ADDRESS:-10.42.0.1/24}"
IP="${ADDR%/*}"

detect_iface(){
  local ifc
  while read -r ifc; do
    [[ -z "$ifc" ]] && continue
    [[ -d "/sys/class/net/$ifc/wireless" ]] && { echo "$ifc"; return 0; }
  done < <(iw dev 2>/dev/null | awk '$1=="Interface"{print $2}')
  return 1
}

stop_all(){
  [[ -f "$RUN/hostapd.pid" ]] && kill "$(cat "$RUN/hostapd.pid")" 2>/dev/null || true
  [[ -f "$RUN/dnsmasq.pid" ]] && kill "$(cat "$RUN/dnsmasq.pid")" 2>/dev/null || true
  rm -f "$RUN/hostapd.pid" "$RUN/dnsmasq.pid"
}

if [[ "$ACTION" == "stop" ]]; then stop_all; exit 0; fi
stop_all

IFACE="${ENDWORLD_WIFI_INTERFACE:-}"
if [[ -z "$IFACE" ]]; then IFACE="$(detect_iface || true)"; fi
if [[ -z "$IFACE" ]]; then
  echo "No Wi-Fi interface found; ENDWORLD remains available over Ethernet/mDNS."
  exit 0
fi
if ! iw list 2>/dev/null | awk '/Supported interface modes:/{f=1;next} f&&/^\t\t \*/{print} f&&!/^\t/{exit}' | grep -q ' AP$'; then
  echo "Wi-Fi interface exists but driver does not advertise AP mode; LAN-only fallback."
  exit 0
fi

rfkill unblock wifi 2>/dev/null || true
ip link set "$IFACE" down
ip addr flush dev "$IFACE" || true
ip addr add "$ADDR" dev "$IFACE"
ip link set "$IFACE" up

cat > "$RUN/hostapd.conf" <<EOF
interface=$IFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=6
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=$PASS
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
country_code=${ENDWORLD_WIFI_COUNTRY:-ES}
ieee80211d=1
EOF

cat > "$RUN/dnsmasq.conf" <<EOF
interface=$IFACE
bind-interfaces
dhcp-range=10.42.0.50,10.42.0.220,255.255.255.0,12h
dhcp-option=3,$IP
dhcp-option=6,$IP
address=/end.world/$IP
address=/wiki.end.world/$IP
address=/ai.end.world/$IP
address=/maps.end.world/$IP
address=/apps.end.world/$IP
address=/sync.end.world/$IP
address=/git.end.world/$IP
address=/#/$IP
no-resolv
domain-needed
bogus-priv
EOF

hostapd -B -P "$RUN/hostapd.pid" "$RUN/hostapd.conf"
dnsmasq --conf-file="$RUN/dnsmasq.conf" --pid-file="$RUN/dnsmasq.pid"
echo "$IFACE" > "$RUN/wifi-interface"
echo "ENDWORLD access point ready: $SSID on $IP"
