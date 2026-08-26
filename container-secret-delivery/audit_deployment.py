#!/usr/bin/env python3
"""
audit_deployment.py — check a GitHub Actions workflow, a Compose file, and (optionally)
the on-host secret files against the container-secret-delivery rules.

    python3 audit_deployment.py --workflow .github/workflows/deploy.yml --compose compose.yaml

Add --host when running ON the deploy host to also check file modes and ownership:

    python3 audit_deployment.py --compose compose.yaml --host --secret-dir /etc/ichin/secrets

Exit codes:  0 = no FAILs   1 = at least one FAIL   2 = bad invocation

This finds patterns. It does not replace judgment — read the findings, then decide.
Requires PyYAML for structural checks; falls back to text scanning without it.
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

FAIL, WARN, INFO, OK = "FAIL", "WARN", "INFO", "OK"
ORDER = {FAIL: 0, WARN: 1, INFO: 2, OK: 3}

SECRETY = re.compile(
    r"(PASSWORD|PASSWD|SECRET|TOKEN|APIKEY|API_KEY|PRIVATE_KEY|CREDENTIAL|"
    r"ACCESS_KEY|CLIENT_SECRET|DSN|CONNECTION_STRING)",
    re.I,
)
# A *_FILE variable holds a path, not a value — exempt it.
FILE_SUFFIX = re.compile(r"_FILE$", re.I)


@dataclass
class Finding:
    severity: str
    rule: str
    where: str
    detail: str
    fix: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, *a, **kw):
        self.findings.append(Finding(*a, **kw))

    def render(self) -> str:
        if not self.findings:
            return "No findings.\n"
        out, counts = [], {FAIL: 0, WARN: 0, INFO: 0, OK: 0}
        for f in sorted(self.findings, key=lambda f: (ORDER[f.severity], f.rule)):
            counts[f.severity] += 1
            out.append(f"[{f.severity:4}] {f.rule}\n         where: {f.where}\n         {f.detail}")
            if f.fix:
                out.append(f"         fix:   {f.fix}")
            out.append("")
        summary = "  ".join(f"{k}={v}" for k, v in counts.items() if v)
        out.append(f"--- {summary} ---")
        return "\n".join(out)

    def worst(self) -> str:
        return min((f.severity for f in self.findings), key=lambda s: ORDER[s], default=OK)


# --------------------------------------------------------------------------- workflow


def audit_workflow(path: Path, rep: Report) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    w = path.name

    # 1. ${{ secrets.X }} interpolated directly inside a run: block.
    #    Expressions are substituted before the temp shell script is generated, so the
    #    plaintext lands on the runner's disk. Also the script-injection surface.
    in_run, run_indent, run_start = False, 0, 0
    for i, line in enumerate(lines, 1):
        m = re.match(r"^(\s*)-?\s*run:\s*[|>]?", line)
        if m:
            in_run, run_indent, run_start = True, len(m.group(1)), i
            if "${{" in line and "secrets." in line:
                rep.add(FAIL, "secret-interpolated-in-run", f"{w}:{i}",
                        "`${{ secrets.* }}` used directly inside a `run:` command.",
                        "Bind it with `env:` and reference $VAR, or pipe it on stdin.")
            continue
        if in_run:
            indent = len(line) - len(line.lstrip())
            if line.strip() and indent <= run_indent:
                in_run = False
            elif "${{" in line and "secrets." in line:
                rep.add(FAIL, "secret-interpolated-in-run", f"{w}:{i}",
                        f"`${{{{ secrets.* }}}}` inside the run: block starting at line {run_start}.",
                        "Bind it with `env:` and reference $VAR, or pipe it on stdin.")

    # 2. echo used to write a secret — trailing newline.
    for i, line in enumerate(lines, 1):
        if not re.search(r"\becho\b", line) or not (">" in line or "|" in line):
            continue
        looks_secret = (
            SECRETY.search(line)
            or "secrets." in line
            or re.search(r"install-secret", line)
        )
        if looks_secret:
            rep.add(WARN, "echo-adds-newline", f"{w}:{i}",
                    "`echo` appends \\n. `$(cat f)` strips it; Python .read() does not — "
                    "the bug appears in one consumer and not another.",
                    "Use printf '%s'.")

    # 3. Secret written under RUNNER_TEMP.
    #    Removing things from RUNNER_TEMP is the recommended scrub step — only flag
    #    lines that put secret material there.
    CLEANUP = re.compile(r"\b(rm|shred|srm|unlink|truncate)\b|-delete\b")
    for i, line in enumerate(lines, 1):
        if CLEANUP.search(line):
            continue
        if re.search(r"(RUNNER_TEMP|runner\.temp)", line) and \
           (SECRETY.search(line) or "install-secret" in line):
            rep.add(FAIL, "secret-in-runner-temp", f"{w}:{i}",
                    "Secret material under RUNNER_TEMP. Documented as emptied at job start "
                    "and end — a Compose bind-mount source there vanishes. Also documented "
                    "as NOT removed when the runner user lacks delete permission, so "
                    "plaintext may linger too.",
                    "Land it in a host-managed path such as /etc/<app>/secrets/.")

    # 4. Secret as a docker CLI argument or build-arg.
    for i, line in enumerate(lines, 1):
        if re.search(r"--build-arg\s+\S*" + SECRETY.pattern, line, re.I):
            rep.add(FAIL, "secret-as-build-arg", f"{w}:{i}",
                    "Build args can be exposed in image history, build metadata, and "
                    "provenance attestations.",
                    "Use RUN --mount=type=secret (BuildKit) instead.")
        if re.search(r"docker\s+(compose\s+)?run.*\s-e\s+\S*" + SECRETY.pattern, line, re.I):
            rep.add(WARN, "secret-on-argv", f"{w}:{i}",
                    "Secret in a command line. On a shared self-hosted runner another job "
                    "can read this via `ps x -w`.",
                    "Pass on stdin or via a file-backed Compose secret.")

    # 5. restart instead of force-recreate after installing a secret.
    #    "installs a secret" = uses the wrapper, OR redirects/pipes something
    #    secret-looking into a file.
    installs = any(
        "install-secret" in l
        or (("secrets." in l or SECRETY.search(l))
            and re.search(r"(>|\|\s*(sudo\s+)?tee)\s*\S*(secret|pass|token|key|cred)",
                          l, re.I))
        for l in lines
    )
    if installs:
        recreates = any("--force-recreate" in l for l in lines)
        restarts = any(re.search(r"compose\s+(-\S+\s+\S+\s+)*restart", l) for l in lines)
        if restarts and not recreates:
            rep.add(FAIL, "restart-wont-reload-secret", w,
                    "Workflow installs a secret then uses `compose restart`. A file-backed "
                    "Compose secret is a bind mount bound to an inode; an atomic mv makes a "
                    "new inode and the running container stays on the old one.",
                    "docker compose up -d --force-recreate --no-deps <service>")
        elif not recreates:
            rep.add(WARN, "no-force-recreate", w,
                    "Workflow installs a secret but never force-recreates. If the value "
                    "changed, the container may keep serving the old one.",
                    "Add --force-recreate --no-deps to the deploy step.")

    # 6. Broad sudo.
    for i, line in enumerate(lines, 1):
        m = re.search(r"sudo\s+(?:-\S+\s+)*(mv|cp|tee|install|dd|chmod|chown|bash|sh)\b", line)
        if m and "install-secret" not in line:
            rep.add(WARN, "broad-sudo", f"{w}:{i}",
                    f"`sudo {m.group(1)}` with caller-controlled paths is close to granting "
                    "the runner root (e.g. `sudo mv /tmp/x /etc/sudoers`).",
                    "Route through a single root-owned wrapper and scope sudoers to it.")

    # 7. Cleanup step.
    if not re.search(r"if:\s*always\(\)", text):
        rep.add(INFO, "no-always-cleanup", w,
                "No `if: always()` step. Self-hosted runners are not guaranteed clean "
                "between jobs.",
                "Add a scrub step that removes any intermediate files.")

    if not HAVE_YAML:
        rep.add(INFO, "yaml-unavailable", w,
                "PyYAML not installed — structural checks skipped (environment gating, "
                "action pinning).", "pip install pyyaml")
        return

    try:
        doc = yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        rep.add(WARN, "workflow-unparseable", w, f"YAML parse error: {e}")
        return

    for job_name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        blob = yaml.safe_dump(job)
        uses_secret = "secrets." in blob

        # 8. Environment gating.
        if uses_secret and not job.get("environment"):
            rep.add(FAIL, "no-environment-gating", f"{w}:jobs.{job_name}",
                    "Job reads secrets but declares no `environment:`. Repository secrets "
                    "have no deployment gate and no deployment history.",
                    "Add `environment: production` and set a deployment branch/tag policy "
                    "on it — the branch policy is available on every plan, unlike "
                    "required reviewers.")

        # 9. Unpinned third-party actions.
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if not uses or uses.startswith("./"):
                continue
            ref = uses.split("@")[-1] if "@" in uses else ""
            if not re.fullmatch(r"[0-9a-f]{40}", ref):
                sev = WARN if uses_secret else INFO
                rep.add(sev, "action-not-pinned", f"{w}:jobs.{job_name}",
                        f"`{uses}` is not pinned to a full-length commit SHA. A tag can be "
                        "moved; a compromised action in a job with secrets reads them all.",
                        "Pin to the 40-character commit SHA.")

    # 10. Deploy on arbitrary branch push.
    on = doc.get("on") or doc.get(True) or {}
    if isinstance(on, dict) and "push" in on:
        push = on["push"] or {}
        if isinstance(push, dict) and "branches" in push and "tags" not in push:
            rep.add(INFO, "deploy-on-branch-push", w,
                    "Deploys trigger on branch push. Combined with an environment branch "
                    "policy this is fine; on its own it widens the set of refs that can "
                    "reach production secrets.",
                    "Prefer tag pushes + workflow_dispatch, and set a deployment branch "
                    "policy on the environment.")


# ---------------------------------------------------------------------------- compose


def audit_compose(path: Path, rep: Report) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    c = path.name

    if not HAVE_YAML:
        rep.add(INFO, "yaml-unavailable", c,
                "PyYAML not installed — Compose checks skipped.", "pip install pyyaml")
        return
    try:
        doc = yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        rep.add(WARN, "compose-unparseable", c, f"YAML parse error: {e}")
        return

    top_secrets = doc.get("secrets") or {}
    services = doc.get("services") or {}

    # 1. Top-level secret sources.
    for name, spec in top_secrets.items():
        if not isinstance(spec, dict):
            continue
        src = spec.get("file")
        if src:
            if re.search(r"(RUNNER_TEMP|runner\.temp|/_temp/|/_work/)", str(src)):
                rep.add(FAIL, "secret-file-in-runner-temp", f"{c}:secrets.{name}",
                        f"`file: {src}` points into the runner work/temp area. That "
                        "directory is emptied at job start and end, so the bind-mount "
                        "source disappears at the next recreate or reboot.",
                        "Point it at a host-managed path such as /etc/<app>/secrets/.")
            elif str(src).startswith("./") or not str(src).startswith(("/", "${", "$")):
                rep.add(WARN, "secret-file-relative-path", f"{c}:secrets.{name}",
                        f"`file: {src}` is relative to the compose file. Workable, but "
                        "couples secret storage to the checkout and is easy to commit by "
                        "accident.",
                        "Use an absolute host path, ideally via ${SECRET_DIR}.")
        elif "environment" in spec:
            rep.add(INFO, "secret-from-environment", f"{c}:secrets.{name}",
                    "Compose materializes this itself. Supported by Compose but not by "
                    "`docker stack deploy`. UNVERIFIED whether the generated file survives "
                    "a host reboot with restart: unless-stopped.",
                    "Test a reboot before relying on this in production.")
        elif spec.get("external"):
            rep.add(INFO, "secret-external", f"{c}:secrets.{name}",
                    "External secret — requires Swarm or an equivalent provider.")

    # 2. Per-service checks.
    for svc, spec in services.items():
        if not isinstance(spec, dict):
            continue
        where = f"{c}:services.{svc}"

        env = spec.get("environment") or {}
        if isinstance(env, list):
            env = dict(
                (kv.split("=", 1) + [""])[:2] for kv in env if isinstance(kv, str)
            )

        # 2a. Secret-looking env vars holding actual values.
        for k, v in env.items():
            if not SECRETY.search(str(k)) or FILE_SUFFIX.search(str(k)):
                continue
            v = str(v) if v is not None else ""
            if v.startswith("${") or v == "":
                rep.add(WARN, "secret-via-environment", f"{where}.environment.{k}",
                        "Secret delivered as an environment variable. Visible to every "
                        "process in the container and via /proc/<pid>/environ; often dumped "
                        "by crash handlers, `docker inspect`, and debug pages.",
                        f"Use a Compose secret and {k}_FILE=/run/secrets/... instead.")
            else:
                rep.add(FAIL, "hardcoded-secret", f"{where}.environment.{k}",
                        "Literal value in a compose file that is presumably in git.",
                        "Move it to a Compose secret; rotate the exposed value.")

        # 2b. env_file may carry values.
        if spec.get("env_file"):
            rep.add(INFO, "env-file-in-use", where,
                    f"`env_file: {spec['env_file']}` — confirm it holds paths and "
                    "non-sensitive config only. Values there are T3.",
                    "Keep secret VALUES in Compose secrets; env_file carries PATHS.")

        declared = set(
            s if isinstance(s, str) else s.get("source")
            for s in (spec.get("secrets") or [])
        )
        for s in declared:
            if s and s not in top_secrets:
                rep.add(FAIL, "undeclared-secret", where,
                        f"Service references secret `{s}` with no top-level definition.",
                        "Add it under the top-level `secrets:` key.")

        # 2c. read_only without tmpfs.
        if spec.get("read_only") and not spec.get("tmpfs"):
            sev = WARN if declared else INFO
            rep.add(sev, "readonly-without-tmpfs", where,
                    "`read_only: true` with no tmpfs. An entrypoint that materializes a "
                    "PGPASSFILE, client cert, or rendered config will fail at startup.",
                    "Add `tmpfs: [/tmp]` if the entrypoint writes anything.")

        # 2d. UID hint.
        if declared and not spec.get("user"):
            rep.add(INFO, "no-explicit-user", where,
                    "Service consumes secrets but sets no `user:`. Bind mounts carry host "
                    "uid/gid into the container, so a non-root image cannot read a 0600 "
                    "file owned by the runner. INFERRED — verify with "
                    "`docker compose exec {} id`.".format(svc),
                    "Set `user:` and chown the host secret file to match.")

        # 2e. Restart policy.
        if not spec.get("restart") and declared:
            rep.add(INFO, "no-restart-policy", where,
                    "No restart policy. Note that adding one makes the bind-mount source "
                    "path a reboot-time dependency — one more reason the source must be a "
                    "persistent host path.",
                    "restart: unless-stopped")

        # 2f. Mutable image reference.
        img = str(spec.get("image") or "")
        if img and "@sha256:" not in img:
            rep.add(INFO, "image-not-digest-pinned", where,
                    f"`{img}` is a mutable tag.",
                    "Pin to an immutable digest for reproducible deploys.")


# ------------------------------------------------------------------------------- host


def audit_host(secret_dir: Path, rep: Report, expect_uid: int | None) -> None:
    where = str(secret_dir)
    if not secret_dir.exists():
        rep.add(FAIL, "secret-dir-missing", where,
                "Secret directory does not exist. Any Compose secret pointing here will "
                "fail at the next recreate.",
                f"sudo install -d -m 0700 -o root -g root {secret_dir}")
        return

    dmode = stat.S_IMODE(secret_dir.stat().st_mode)
    if dmode & 0o077:
        rep.add(WARN, "secret-dir-permissive", where,
                f"Directory mode is {dmode:04o}; group/other have access.",
                f"sudo chmod 0700 {secret_dir}")
    else:
        rep.add(OK, "secret-dir-mode", where, f"mode {dmode:04o}")

    files = [p for p in secret_dir.iterdir() if p.is_file() and not p.name.startswith(".")]
    if not files:
        rep.add(WARN, "no-secret-files", where, "Directory is empty.")
        return

    for p in files:
        st = p.stat()
        mode = stat.S_IMODE(st.st_mode)
        w = str(p)

        if mode & 0o077:
            rep.add(FAIL, "secret-file-permissive", w,
                    f"Mode {mode:04o} allows group/other access. Postgres SILENTLY ignores "
                    "a passfile with permissions this wide — you get an auth failure with "
                    "no explanation.",
                    f"sudo chmod 0600 {p}")

        if st.st_size == 0:
            rep.add(FAIL, "secret-file-empty", w,
                    "Empty file. Almost always an unset CI secret. The service will start "
                    "with a blank credential and may look healthy.",
                    "Confirm the secret is set on the GitHub environment, then redeploy.")
            continue

        data = p.read_bytes() if os.access(p, os.R_OK) else None
        if data is None:
            rep.add(INFO, "secret-unreadable-by-auditor", w,
                    "Cannot read (expected if not running as root). Content checks skipped.",
                    "Re-run with sudo for content checks.")
        else:
            if data.endswith(b"\n") or data.endswith(b"\r\n"):
                rep.add(WARN, "trailing-newline", w,
                        "File ends with a newline. `$(cat f)` strips it but Python .read() "
                        "does not — the failure shows up in one consumer and not another.",
                        "Rewrite with printf '%s' (no trailing newline).")
            if not data.strip():
                rep.add(FAIL, "secret-whitespace-only", w,
                        "Whitespace-only content — almost certainly an unset variable.")

        if expect_uid is not None and st.st_uid != expect_uid:
            rep.add(WARN, "owner-uid-mismatch", w,
                    f"Owned by uid {st.st_uid}, expected {expect_uid}. A bind mount carries "
                    "host uid/gid into the container, so a non-root container cannot read "
                    "another user's 0600 file.",
                    f"sudo chown {expect_uid} {p}")
        else:
            rep.add(INFO, "owner-uid", w,
                    f"uid={st.st_uid} gid={st.st_gid} mode={mode:04o}. Compare against "
                    "`docker compose exec <svc> id`.")


# ------------------------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workflow", type=Path, action="append", default=[],
                    help="Path to a workflow YAML (repeatable)")
    ap.add_argument("--compose", type=Path, action="append", default=[],
                    help="Path to a compose file (repeatable)")
    ap.add_argument("--host", action="store_true",
                    help="Also check on-host secret files (run on the deploy host)")
    ap.add_argument("--secret-dir", type=Path, default=Path("/etc/ichin/secrets"))
    ap.add_argument("--expect-uid", type=int, default=None,
                    help="UID the container runs as; checks secret file ownership")
    args = ap.parse_args()

    if not (args.workflow or args.compose or args.host):
        ap.print_help()
        return 2

    rep = Report()
    for p in args.workflow:
        if p.exists():
            audit_workflow(p, rep)
        else:
            rep.add(WARN, "file-missing", str(p), "Workflow not found.")
    for p in args.compose:
        if p.exists():
            audit_compose(p, rep)
        else:
            rep.add(WARN, "file-missing", str(p), "Compose file not found.")
    if args.host:
        audit_host(args.secret_dir, rep, args.expect_uid)

    print(rep.render())

    if rep.worst() == FAIL:
        print("\nAt least one FAIL. Fix before the next deploy.")
        return 1
    print("\nNo FAILs. Review WARN/INFO items and decide which to schedule.")
    print("Remember the residual risk statement for your tier (see SKILL.md, Mode C).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
