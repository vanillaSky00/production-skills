#!/usr/bin/env bash
#
# verify_bind_mount_rotation.sh
#
# Turns an INFERENCE into a fact about YOUR environment.
#
# The claim under test:
#   A file-backed Compose secret is delivered as a bind mount. A bind mount resolves the
#   pathname once and thereafter refers to the INODE. So an atomic `mv` produces a new
#   inode, and the running container keeps serving the OLD value until it is recreated —
#   and `docker compose restart` is not guaranteed to fix that.
#
# Docker documents the bind-mount delivery. The inode-binding consequence is inferred.
# Before writing it into a team guideline, verify it here.
#
# Safe to run: throwaway project name, dummy values, cleans up after itself.
# Requires: docker + compose v2. Does NOT need root unless your docker does.
#
#     bash verify_bind_mount_rotation.sh
#
set -euo pipefail

PROJECT="secretverify$$"
WORKDIR="$(mktemp -d)"
OLD_VALUE="OLD-VALUE-$(date +%s)"
NEW_VALUE="NEW-VALUE-$(date +%s)-rotated"

cleanup() {
  docker compose -p "$PROJECT" -f "$WORKDIR/compose.yaml" down -v --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$WORKDIR"
}
trap cleanup EXIT

command -v docker >/dev/null || { echo "docker not found"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "docker compose v2 not found"; exit 1; }

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
step() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

step "Setup"
printf '%s' "$OLD_VALUE" > "$WORKDIR/thesecret"
chmod 0600 "$WORKDIR/thesecret"
echo "secret file : $WORKDIR/thesecret"
echo "initial inode: $(stat -c %i "$WORKDIR/thesecret")"

cat > "$WORKDIR/compose.yaml" <<EOF
services:
  probe:
    image: busybox:stable
    command: ["sh", "-c", "while true; do sleep 3600; done"]
    secrets: [thesecret]
secrets:
  thesecret:
    file: $WORKDIR/thesecret
EOF

read_secret() {
  docker compose -p "$PROJECT" -f "$WORKDIR/compose.yaml" \
    exec -T probe cat /run/secrets/thesecret 2>/dev/null || echo "<unreadable>"
}

step "1. Start container and confirm mount type"
docker compose -p "$PROJECT" -f "$WORKDIR/compose.yaml" up -d >/dev/null 2>&1
sleep 2

CID="$(docker compose -p "$PROJECT" -f "$WORKDIR/compose.yaml" ps -q probe)"
MOUNT_TYPE="$(docker inspect "$CID" \
  --format '{{range .Mounts}}{{if eq .Destination "/run/secrets/thesecret"}}{{.Type}}{{end}}{{end}}')"
echo "mount type at /run/secrets/thesecret : ${MOUNT_TYPE:-<none>}"

V0="$(read_secret)"
echo "container sees                      : $V0"
[ "$V0" = "$OLD_VALUE" ] || { echo "FAILED: container did not see the initial value"; exit 1; }

step "2. Atomic replace on the host (what install-secret does)"
printf '%s' "$NEW_VALUE" > "$WORKDIR/.thesecret.tmp"
chmod 0600 "$WORKDIR/.thesecret.tmp"
mv -f "$WORKDIR/.thesecret.tmp" "$WORKDIR/thesecret"
echo "new inode  : $(stat -c %i "$WORKDIR/thesecret")"
echo "host value : $(cat "$WORKDIR/thesecret")"

V1="$(read_secret)"
echo "container sees after mv (no action) : $V1"

step "3. docker compose restart"
docker compose -p "$PROJECT" -f "$WORKDIR/compose.yaml" restart probe >/dev/null 2>&1
sleep 2
V2="$(read_secret)"
echo "container sees after restart        : $V2"

step "4. docker compose up -d --force-recreate --no-deps"
docker compose -p "$PROJECT" -f "$WORKDIR/compose.yaml" up -d --force-recreate --no-deps probe >/dev/null 2>&1
sleep 2
V3="$(read_secret)"
echo "container sees after force-recreate : $V3"

verdict() { [ "$1" = "$NEW_VALUE" ] && echo "NEW" || { [ "$1" = "$OLD_VALUE" ] && echo "OLD" || echo "OTHER"; }; }

step "RESULTS"
printf '%-38s %s\n' "mount type"                     "${MOUNT_TYPE:-<none>}"
printf '%-38s %s\n' "after atomic mv, no action"     "$(verdict "$V1")"
printf '%-38s %s\n' "after compose restart"          "$(verdict "$V2")"
printf '%-38s %s\n' "after compose up --force-recreate" "$(verdict "$V3")"

echo
if [ "$(verdict "$V1")" = "OLD" ]; then
  bold "CONFIRMED: bind mount follows the inode, not the pathname."
  echo "  An atomic mv alone does NOT reach a running container."
else
  bold "NOT CONFIRMED on this host: the running container picked up the new value"
  echo "  without any action. Do not assume this holds across docker versions or"
  echo "  storage drivers — still recreate on rotation."
fi

echo
if [ "$(verdict "$V2")" = "NEW" ]; then
  echo "  \`compose restart\` DID pick up the new value on this host+version."
  echo "  Still do not depend on it: it is an implementation detail, not a documented"
  echo "  contract, and it can change between docker releases."
else
  bold "  \`compose restart\` did NOT pick up the new value. This is the trap:"
  echo "  the command succeeds, and the container keeps serving the old credential"
  echo "  until the old one is revoked."
fi

echo
if [ "$(verdict "$V3")" = "NEW" ]; then
  bold "  \`up -d --force-recreate\` picked up the new value. Use this for rotation."
else
  bold "  UNEXPECTED: force-recreate did not pick up the new value. Investigate before"
  echo "  rotating anything in production."
fi

cat <<'EOF'

Rotation rule to write into the guideline:

    path unchanged
       -> atomic replace secret file      (new inode)
       -> docker compose up -d --force-recreate --no-deps <service>

Record the docker version alongside this result — the finding is version-specific:
EOF
docker version --format '    docker {{.Server.Version}} / compose plugin' 2>/dev/null || true
docker compose version --short 2>/dev/null | sed 's/^/    compose /' || true
