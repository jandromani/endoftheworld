#!/usr/bin/env bash
set -euo pipefail

log(){
  local line="[NANO-MINI] $*"
  printf '%s\n' "$line"
  if [[ -w /dev/ttyS0 ]]; then printf '%s\n' "$line" > /dev/ttyS0 || true; fi
}
finish(){
  local rc=$?
  if (( rc != 0 )); then log "THE_ARK_OFFLINE_SMOKE=FAIL rc=$rc"; fi
  sync
  systemctl poweroff --no-block || true
  exit "$rc"
}
trap finish EXIT

wait_url(){
  local url="$1"
  log "waiting for $url"
  for _ in $(seq 1 30); do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      log "ready $url"
      return 0
    fi
    sleep 1
  done
  log "TIMEOUT $url"
  {
    echo "===== SYSTEMD STATUS ====="
    systemctl --no-pager --full status endworld-portal.service endworld-stack.service docker.service || true
    echo "===== STACK JOURNAL ====="
    journalctl -b --no-pager -n 160 -u endworld-stack.service -u docker.service || true
    echo "===== DOCKER PS ====="
    docker ps -a || true
    echo "===== KIWIX LOG ====="
    docker logs --tail 120 endworld-kiwix 2>&1 || true
  } | while IFS= read -r line; do log "$line"; done
  return 1
}

log "offline smoke starting"
wait_url http://127.0.0.1/health
wait_url http://127.0.0.1:8081/
wait_url http://127.0.0.1:8082/health
wait_url http://127.0.0.1:8083/

curl -fsS http://127.0.0.1/api/status >/tmp/status.json
python3 - <<'PY'
import json
s=json.load(open("/tmp/status.json"))
assert s["internet"] is False, s
assert s["services"]["portal"] and s["services"]["knowledge"] and s["services"]["ai"] and s["services"]["voice"], s
assert s["map_ready"], s
PY

curl -fsS http://127.0.0.1/map.html >/dev/null
curl -fsS http://127.0.0.1/api/maps >/tmp/maps.json
python3 - <<'PY'
import json
m=json.load(open("/tmp/maps.json"))
assert any(x["id"]=="spain" for x in m),m
PY
code="$(curl -sS -o /tmp/map-range -w '%{http_code}' -H 'Range: bytes=0-31' http://127.0.0.1/maps/spain.pmtiles)"
[[ "$code" == "206" && "$(stat -c %s /tmp/map-range)" == "32" ]]

curl -fsS -H 'Content-Type: application/json' -d '{"messages":[{"role":"user","content":"hola"}]}' http://127.0.0.1/api/chat >/tmp/chat.json
grep -q 'mini-ai-ok' /tmp/chat.json

curl -fsS -H 'Content-Type: application/json' -d '{"question":"como trato una quemadura"}' http://127.0.0.1/api/ask >/tmp/ask.json
python3 - <<'PY'
import json
x=json.load(open("/tmp/ask.json"))
assert "mini-ai-ok" in x["answer"],x
assert any(s.get("kind")=="kiwix-article" for s in x.get("sources",[])),x
PY

printf 'RIFF....WAVEfmt ' >/tmp/test.wav
curl -fsS -F "file=@/tmp/test.wav;type=audio/wav" http://127.0.0.1/api/transcribe >/tmp/voice.json
grep -q 'mini-whisper-ok' /tmp/voice.json

state_code="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/vault/state/private/secret.txt)"
[[ "$state_code" == "403" ]]


log "running offline agent acceptance task"
if ! python3 /opt/endworld/scripts/agent_runner.py \
  --vault /srv/endworld --profile nano-mini --task-id nano-mini-agent-ci --json \
  "Find the local burn-treatment guidance, cite the frozen source, write a field note, and confirm whether Internet is available." \
  >/tmp/agent.json 2>&1; then
  while IFS= read -r line; do log "AGENT: $line"; done </tmp/agent.json
  exit 1
fi
python3 - <<'PY'
import json,pathlib
x=json.load(open("/tmp/agent.json"))
assert x["ok"] is True,x
assert "[E1]" in x["answer"],x
note=pathlib.Path("/srv/endworld/state/agent/workspace/burn-field-note.md")
assert note.is_file(),note
text=note.read_text(encoding="utf-8")
assert "[E1]" in text and "quemadura" in text.lower(),text
events=pathlib.Path("/srv/endworld/state/agent/tasks/nano-mini-agent-ci/events.jsonl").read_text(encoding="utf-8")
assert '"tool": "ark.search"' in events,events
assert '"tool": "ark.read_source"' in events,events
assert '"tool": "ark.write_note"' in events,events
assert '"tool": "ark.status"' in events,events
assert '"internet": false' in events,events
PY
python3 /opt/endworld/scripts/agent_runner.py \
  --vault /srv/endworld --profile nano-mini --policy-selftest >/tmp/agent-policy.json
python3 - <<'PY'
import json
x=json.load(open("/tmp/agent-policy.json"))
assert x["ok"] is True,x
assert "os.shell" in x["denied"],x
PY
log "THE_ARK_AGENT_OFFLINE_SMOKE=PASS"

log "THE_ARK_OFFLINE_SMOKE=PASS"
