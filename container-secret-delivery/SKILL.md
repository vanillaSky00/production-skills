---
name: container-secret-delivery
description: Design, implement, audit, and rotate the path a secret takes from GitHub Actions into a running container deployed with Docker Compose. Use this whenever the user passes a password, token, key, or credential to a container; writes or reviews a deploy workflow that touches `secrets.*`; adds a new service to an existing deploy host; asks where a DB password or API key should live; rotates a credential; or debugs a container that cannot read `/run/secrets/...`. Also use it for any "does this look right?" review of a compose file or Actions workflow that handles credentials, and whenever the user mentions self-hosted runners, `RUNNER_TEMP`, bind-mounted secret files, `_FILE` env conventions, `PGPASSFILE`, Compose `secrets:`, OIDC, Secrets Manager, or RDS IAM auth. Prefer this skill over ad-hoc advice — the failure modes here are silent and show up weeks after deploy.
---

# Container secret delivery

A secret's journey has four legs: **store → transport → land → consume**, plus a fifth
concern that most guides omit, **rotate**. Most production incidents come from the last
two, not the first two. People get "use GitHub Secrets" right and then bind-mount the
file from a directory that gets wiped, or replace the file and never recreate the
container.

Work in one of five modes. Identify which one applies from what the user is asking, then
follow that section. Do not dump the whole tier model on someone who just wants to know
why their container can't read a file.

| Mode | Trigger | Go to |
|---|---|---|
| **A. Choose** | New service, "where should this password live?" | [Mode A](#mode-a-choose-a-tier) |
| **B. Implement** | "Set this up", building the deploy workflow | [Mode B](#mode-b-implement) |
| **C. Audit** | "Does this look right?", reviewing existing config | [Mode C](#mode-c-audit) |
| **D. Rotate** | "Rotate the DB password", credential expiry | [Mode D](#mode-d-rotate) |
| **E. Debug** | Container can't read the secret, auth failing | [Mode E](#mode-e-debug) |

---

## The one-line principle

> **The runner's workspace and temp directories must never be the persistent source of a
> secret.** Persistent secrets need an explicit host-managed path or a secret manager.

Note the phrasing: this is a boundary of *responsibility*, not of *machines*. A
self-hosted runner is frequently installed on the very host it deploys to. Same machine,
different roles. Do not tell the user "the runner is not the deploy host" — it often is.

Why `RUNNER_TEMP` specifically fails, from GitHub's own reference: the directory *"is
emptied at the beginning and end of each job"*, and *"files will not be removed if the
runner's user account does not have permission to delete them."* One path that guarantees
neither persistence nor cleanup is the worst possible home for a credential — the Compose
bind mount source vanishes, **and** plaintext may linger anyway.

---

## Mode A: Choose a tier

Ask two questions, in this order:

1. Is there a cloud IAM / workload identity available to the **running container** (EC2
   instance role, ECS task role, K8s service account, Vault agent)?
2. Does the target image read secrets from a file, or only from environment variables?

| Tier | Path | Use when |
|---|---|---|
| **T0** | Runtime IAM identity → Secrets Manager / RDS IAM auth | Q1 = yes. **Production target.** |
| **T1** | GH Environment Secret → host secret file → Compose `secrets:` | Q1 = no. Self-hosted, no IdP. |
| **T2** | GH Environment Secret → container env var | Q2 = env-only and no wrapper is viable |
| **T3** | Committed `.env`, CLI arg, `--build-arg` | Never. Flag as a defect. |

The decisive property of T0 is not "shorter-lived credentials." It is that **deploy
identity and runtime identity are separate**. The CI pipeline gets permission to deploy;
the container gets permission to read its own credential. The DB password never passes
through GitHub Actions at all. A design that routes the DB secret through OIDC → Secrets
Manager → runner → file is better than T1, but it is still one compromised workflow away
from the database. Say so plainly.

Read `references/tiers.md` for the full comparison, the migration path from T1 to T0, and
the credential-lifetime numbers (which are commonly misquoted — see the table there
before stating any duration).

---

## Mode B: Implement

Default to **T1** unless Mode A selected otherwise. Full step-by-step, with rationale for
every line, is in `references/t1-implementation.md`. Read it before writing config.

Templates to copy and adapt:

| File | Purpose |
|---|---|
| `assets/install-secret.sh` | Root-owned wrapper that lands the secret. Edit the `OWNER` map at the top. |
| `assets/sudoers.d-deploy-secrets` | The single sudoers line that makes the wrapper safe |
| `assets/workflow-deploy.yml` | GitHub Actions deploy job |
| `assets/compose-fragment.yaml` | Service + top-level `secrets:` wiring |

### Non-negotiables

These are the ones that fail silently. Everything else is style.

| Rule | What breaks without it |
|---|---|
| `env:` indirection, never `${{ secrets.X }}` inline in `run:` | Value gets written into a temp shell script on the runner; also the script-injection surface |
| Land in a host-managed path, not `RUNNER_TEMP` | Bind mount source disappears on the next recreate or reboot |
| `printf '%s'`, not `echo` | Trailing `\n`. `$(cat f)` strips it, Python `.read()` does not — the failure appears in one consumer and not another |
| `chmod 0600` explicitly, don't rely on `umask` | `umask` only affects *creation*; a pre-existing file keeps its old mode |
| Atomic `mv` into place | A container starting mid-write reads a truncated secret |
| `chown` to the **container's** UID | Bind mounts carry host uid/gid inside. A non-root container cannot read someone else's `0600` file |
| Reject empty input | Unset secret → empty file → service starts with a blank password and *appears* healthy |
| Scope the sudoers entry to one wrapper | `sudo mv` with arbitrary paths is equivalent to giving the runner root |
| `tmpfs: [/tmp]` when `read_only: true` | Entrypoints that materialize `PGPASSFILE` or similar fail at startup |

### Consumption patterns

| Image type | How it reads the secret |
|---|---|
| Official images (postgres, mysql, redis…) | `<VAR>_FILE=/run/secrets/x` — a convention those images implement, not a Docker feature |
| Your own services | Read `/run/secrets/x` directly, or support the `_FILE` convention. **Add `_FILE` support to in-house services** — one-time cost, makes every deployment path uniform |
| libpq consumers (psycopg, MLflow backend store) | `PGPASSFILE`. Postgres *silently ignores* a passfile with group/world access, so the mode matters more than usual |
| Third-party image with no file support | Entrypoint wrapper: read file → `export` → `exec` the real process. Second-best, but the value never leaves the container |

---

## Mode C: Audit

Run the static checker, then interpret. Do not hand the user raw script output — the
script finds patterns, the judgment is yours.

```bash
python3 scripts/audit_deployment.py \
  --workflow .github/workflows/deploy.yml \
  --compose compose.yaml
```

Add `--host` when running **on the deploy host itself** to also check file modes,
ownership, emptiness, and trailing newlines:

```bash
python3 scripts/audit_deployment.py --compose compose.yaml --host --secret-dir /etc/ichin/secrets
```

Severities: `FAIL` = fix before next deploy. `WARN` = defect, schedule it. `INFO` =
hardening opportunity.

After reporting findings, always state the **residual risk** of whatever tier they are on.
For T1 that sentence is: *the GitHub Actions pipeline holds the plaintext production
credential; anyone who can run arbitrary code in a workflow can obtain it.* Do not bury
this. It is the honest reason T0 exists, and it turns "we're secure" into "we've accepted
a known risk with these compensating controls."

Compensating controls to check for on a T1 setup:

- Environment secret with a **deployment branch policy** (available on all plans, unlike
  required reviewers — see `references/github-controls.md`)
- CODEOWNERS covering `.github/workflows/`
- Scoped sudoers wrapper rather than blanket `sudo`
- Least-privilege DB role (not superuser)
- Runner hardening: private repos only, runner groups, JIT/ephemeral, no unrelated
  credentials on the box

---

## Mode D: Rotate

This is where the most common wrong answer lives. `docker compose restart` is **not**
sufficient.

Docker delivers a file-backed Compose secret as a **bind mount**, and a bind mount binds
to an **inode**, not to a pathname. An atomic `mv` creates a new inode and repoints the
directory entry. The already-running container is still mounted on the old inode.

```
path unchanged
   ↓
atomic replace secret file   (new inode)
   ↓
recreate the consuming container   (mount re-resolved)
```

```bash
docker compose up -d --force-recreate --no-deps <service>
```

`--no-deps` limits the blast radius to the one service instead of dragging its Postgres
and Redis dependencies through a restart.

The inode-binding claim is a **mechanical inference**, not something Docker documents
explicitly. Before writing it into a team guideline, have the user verify it once in
their own environment:

```bash
bash scripts/verify_bind_mount_rotation.sh
```

It stands up a throwaway container, replaces the secret, and reports what each of
`restart` / `force-recreate` actually does. Ten minutes, and the rule graduates from
inference to established fact for their stack.

The ordered runbook — including the new-credential-first, revoke-last sequencing that
makes rotation zero-downtime — is in `references/rotation.md`. Read it before running a
production rotation; the ordering matters more than the commands.

---

## Mode E: Debug

Work outward from the container. Most reports of "the secret isn't working" are one of
five things:

| Symptom | Likely cause | Check |
|---|---|---|
| `Permission denied` on `/run/secrets/x` | Host file owned by the runner UID, container runs as a different UID | `docker compose exec svc id` vs `stat -c '%u:%g %a' <hostfile>` |
| `no such file or directory` at startup | Bind mount source was deleted — classic `RUNNER_TEMP` symptom | `ls -l` the source path on the host |
| Auth fails but the password "looks right" | Trailing newline from `echo` | `tail -c1 <hostfile> \| od -An -tx1` — `0a` means a stray newline |
| Postgres ignores the passfile, no error | Mode wider than `0600`; Postgres ignores it silently | `stat -c %a` the passfile *inside* the container |
| Rotated the secret, container still uses the old one | Bind mount still on the old inode | Mode D — force-recreate |
| Service starts, connects as nobody, odd errors | Empty secret file from an unset GitHub secret | `wc -c <hostfile>` |

Always read the value **as the container sees it**, not as the host sees it:

```bash
docker compose exec <svc> sh -c 'ls -l /run/secrets/ && wc -c /run/secrets/x'
```

Never `cat` a secret into the conversation or into CI logs. Compare lengths and checksums
instead:

```bash
docker compose exec <svc> sh -c 'sha256sum /run/secrets/x' ; sudo sha256sum /etc/ichin/secrets/x
```

---

## Reference files

Read these when the mode calls for them, not upfront.

| File | Read when |
|---|---|
| `references/tiers.md` | Mode A, or whenever tier trade-offs or credential lifetimes come up |
| `references/t1-implementation.md` | Mode B — full walkthrough with rationale |
| `references/rotation.md` | Mode D — ordered runbook and the bind-mount mechanism |
| `references/github-controls.md` | Environment secrets, branch policy, self-hosted runner hardening |

## Sourcing discipline

This domain is full of confidently-stated folklore. When making a claim, separate what is
documented from what is inferred:

- **Documented**: Compose delivers secrets by bind-mounting a single file; `RUNNER_TEMP`
  is emptied at job start and end; Postgres ignores overly-permissive passfiles;
  environment secrets can be gated by required reviewers; structured data makes log
  redaction unreliable.
- **Inferred, verify locally**: bind mounts bind to inodes so `mv` needs a recreate; the
  container UID must own the file; `docker compose restart` does not re-resolve the mount.
- **Frequently misquoted**: credential lifetimes. See the table in `references/tiers.md`
  before stating any number.

Flag which is which. The user is going to put this in a team document, and an unmarked
inference that turns out to be wrong costs more than one that was labelled honestly.
