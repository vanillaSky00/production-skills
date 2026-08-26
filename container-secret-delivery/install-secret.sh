#!/bin/bash
#
# install-secret — land a secret from stdin into a host-managed secret directory.
#
# Install as root:
#     sudo install -m 0755 -o root -g root install-secret.sh /usr/local/sbin/install-secret
#
# Grant to the runner user via /etc/sudoers.d/deploy-secrets (see the sibling asset).
#
# Usage:
#     printf '%s' "$VALUE" | sudo /usr/local/sbin/install-secret <name>
#
# Design constraints — do not relax these without understanding why they exist:
#   * Input arrives ONLY on stdin. The caller can never supply a source path, so this
#     cannot be turned into an arbitrary "move any file anywhere as root" primitive.
#   * The target directory is hardcoded. Nothing the caller supplies reaches a path.
#   * Secret names come from an explicit map, not a regex. Unknown names are rejected by
#     construction, and the map doubles as the per-secret owner UID/GID.
#   * Empty input is refused. An unset CI secret would otherwise produce an empty file and
#     a service that starts with a blank credential and looks healthy.
#   * Mode and ownership are set BEFORE the rename, so the file is never briefly visible
#     at its final path with the wrong permissions.
#   * The rename is atomic within one filesystem, so a container starting mid-write can
#     never read a truncated secret.
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — edit for this host.
# ---------------------------------------------------------------------------

SECRET_DIR=/etc/ichin/secrets

# name -> uid:gid of the container user that must read it.
# Find a container's UID with:  docker compose exec <svc> id
declare -A OWNER=(
  [mlflow_db_password]=10001:10001
  [dagster_db_password]=10002:10002
  [api_db_password]=10003:10003
)

# ---------------------------------------------------------------------------

die() { printf 'install-secret: %s\n' "$1" >&2; exit "${2:-1}"; }

name="${1:-}"
[[ -n "$name" ]] || die "usage: install-secret <name>   (value on stdin)" 2

if [[ -z "${OWNER[$name]:-}" ]]; then
  die "unknown secret name '$name'; add it to the OWNER map in $0" 2
fi

[[ ! -t 0 ]] || die "refusing to read from a terminal; pipe the value on stdin" 2

install -d -m 0700 -o root -g root "$SECRET_DIR"

umask 077
tmp="$(mktemp "$SECRET_DIR/.${name}.XXXXXX")"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

cat > "$tmp"

[[ -s "$tmp" ]] || die "refusing to install an empty value for '$name'" 3

# Reject a value that is only whitespace — almost always an unset variable.
if [[ -z "$(tr -d '[:space:]' < "$tmp")" ]]; then
  die "refusing to install a whitespace-only value for '$name'" 3
fi

chmod 0600 "$tmp"
chown "${OWNER[$name]}" "$tmp"

if [[ -f "$SECRET_DIR/$name" ]] \
   && cmp -s "$tmp" "$SECRET_DIR/$name"; then
  printf 'install-secret: %s unchanged\n' "$name"
  exit 0
fi

mv -f "$tmp" "$SECRET_DIR/$name"     # atomic replace: NEW INODE
trap - EXIT

printf 'install-secret: %s installed (%s bytes, sha256 %s)\n' \
  "$name" \
  "$(stat -c %s "$SECRET_DIR/$name")" \
  "$(sha256sum "$SECRET_DIR/$name" | cut -c1-16)"

cat >&2 <<'EOF'

  NOTE: the secret file now has a new inode. A running container is still
  bind-mounted on the OLD inode and will keep serving the old value.

      docker compose up -d --force-recreate --no-deps <service>

  A plain `docker compose restart` is NOT guaranteed to pick this up.
EOF
