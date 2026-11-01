#!/bin/bash
#
# install-secret — land a secret value from stdin into a host-managed secret directory.
#
# This script is GENERIC. Do not edit it per project. All project-specific values live in
# the config file below, which is root-owned and not writable by the deploy account.
#
#   install:  sudo install -m 0755 -o root -g root install-secret.sh /usr/local/sbin/install-secret
#   config:   /etc/deploy-secrets.conf     (root:root 0644 — see deploy-secrets.conf template)
#   grant:    /etc/sudoers.d/deploy-secrets
#
#   usage:    printf '%s' "$VALUE" | sudo /usr/local/sbin/install-secret <name>
#
# Design constraints — do not relax these without understanding why they exist:
#
#   * Input arrives ONLY on stdin. The caller can never supply a source path, so this
#     cannot be turned into an arbitrary "move any file anywhere as root" primitive.
#   * The CONFIG PATH is hardcoded. Config content is root-controlled, so moving the
#     project settings into a file does not hand the caller any influence over paths.
#     A `--config` flag would undo the entire security property; there is deliberately
#     no such flag.
#   * Secret names come from an explicit table, not a pattern. Unknown names are rejected
#     by construction, and the table carries the per-secret owner and directory.
#   * Empty input is refused. An unset CI secret would otherwise produce an empty file and
#     a service that starts with a blank credential and looks healthy.
#   * Mode and ownership are set BEFORE the rename, so the file is never briefly visible
#     at its final path with the wrong permissions.
#   * The rename is atomic within one filesystem, so a container starting mid-write can
#     never read a truncated secret.
#
set -euo pipefail

CONFIG=/etc/deploy-secrets.conf     # hardcoded on purpose; see above

die() { printf 'install-secret: %s\n' "$1" >&2; exit "${2:-1}"; }

name="${1:-}"
[[ -n "$name" ]] || die "usage: install-secret <name>   (value on stdin)" 2
[[ $# -eq 1 ]] || die "unexpected extra arguments; value goes on stdin, not argv" 2
[[ ! -t 0 ]] || die "refusing to read from a terminal; pipe the value on stdin" 2

[[ -r "$CONFIG" ]] || die "config not readable: $CONFIG" 4

# Refuse a config the deploy account could tamper with — otherwise the allowlist is
# meaningless and this becomes a write-anywhere primitive after all.
cfg_stat="$(stat -c '%u %a' "$CONFIG")"
cfg_uid="${cfg_stat%% *}"; cfg_mode="${cfg_stat##* }"
[[ "$cfg_uid" == "0" ]] || die "$CONFIG must be owned by root (uid 0), found uid $cfg_uid" 4
(( 8#$cfg_mode & 0022 )) && die "$CONFIG is group/world writable (mode $cfg_mode)" 4

# ---------------------------------------------------------------------------
# Parse config. Plain field parsing, never `source` — a sourced config file is a
# code-execution surface even when root-owned.
#
#   secret_dir = /etc/myapp/secrets
#   <name>  <uid:gid>  [dir]
# ---------------------------------------------------------------------------
default_dir=""; owner=""; target_dir=""; found=0

while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="$(printf '%s' "$line" | tr -s '[:space:]' ' ')"
  line="${line# }"; line="${line% }"
  [[ -n "$line" ]] || continue

  if [[ "$line" == secret_dir\ =\ * || "$line" == secret_dir=* ]]; then
    default_dir="${line#*=}"; default_dir="${default_dir# }"
    continue
  fi

  read -r f_name f_owner f_dir <<<"$line"
  [[ "$f_name" == "$name" ]] || continue
  [[ "$found" -eq 0 ]] || die "duplicate entry for '$name' in $CONFIG" 4
  owner="$f_owner"; target_dir="${f_dir:-}"; found=1
done < "$CONFIG"

(( found )) || die "unknown secret name '$name'; add it to $CONFIG" 2
[[ "$owner" =~ ^[0-9]+:[0-9]+$ ]] || die "entry '$name' needs a numeric uid:gid, got '$owner'" 4

target_dir="${target_dir:-$default_dir}"
[[ -n "$target_dir" ]] || die "no directory for '$name' and no secret_dir set in $CONFIG" 4
[[ "$target_dir" == /* ]] || die "directory for '$name' must be absolute, got '$target_dir'" 4

install -d -m 0700 -o root -g root "$target_dir"

umask 077
tmp="$(mktemp "$target_dir/.${name}.XXXXXX")"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

cat > "$tmp"

[[ -s "$tmp" ]] || die "refusing to install an empty value for '$name'" 3
[[ -n "$(tr -d '[:space:]' < "$tmp")" ]] || \
  die "refusing to install a whitespace-only value for '$name'" 3

chmod 0600 "$tmp"
chown "$owner" "$tmp"

if [[ -f "$target_dir/$name" ]] && cmp -s "$tmp" "$target_dir/$name"; then
  printf 'install-secret: %s unchanged\n' "$name"
  exit 0
fi

mv -f "$tmp" "$target_dir/$name"     # atomic replace: NEW INODE
trap - EXIT

printf 'install-secret: %s -> %s (%s bytes, sha256 %s, owner %s)\n' \
  "$name" "$target_dir/$name" \
  "$(stat -c %s "$target_dir/$name")" \
  "$(sha256sum "$target_dir/$name" | cut -c1-16)" \
  "$owner"

cat >&2 <<'EOF'

  NOTE: the secret file now has a new inode. A running container is still
  bind-mounted on the OLD inode and will keep serving the old value.

      docker compose up -d --force-recreate --no-deps <service>

  A plain `docker compose restart` is NOT guaranteed to pick this up.
EOF
