---
name: docker-github-actions-deploy
description: Deploy or update a self-hosted service using Docker Compose and GitHub Actions self-hosted runners, with configuration from GitHub Environment variables and secrets. Use when asked to containerize, provision, deploy, redeploy, or operationalize a service on local/on-prem or cloud Docker hosts through GitHub Actions.
---

# Docker Service Deployment via GitHub Actions

Deploy **any service** safely and reproducibly to an existing self-hosted Docker machine. Reuse repository conventions and prefer the smallest maintainable implementation.

## Inputs and discovery

Before editing, inspect the repository, existing Compose files, workflows, runner labels, GitHub Environments, deployment directories, proxy/network conventions, and operational docs. Identify:

- Service name, official image/source, pinned version, and official deployment/configuration/upgrade documentation.
- Target host(s), deployment topology, reachable endpoints, and runner-to-host execution route.
- Ports, dependencies, persistent volumes, resource needs, health/readiness checks, backup requirements, and failure modes.
- GitHub Environment names, nonsecret variables, secrets, and which values need bootstrapping.

Use available facts; do not invent credentials, addresses, runner labels, or existing infrastructure. Ask for *only* missing blockers if implementation cannot safely proceed. If a host is unreachable or permissions are unavailable, generate runnable files and clearly mark unverified steps.

## Deployment decisions

1. Prefer **one Docker Compose project per independent service or stack**, with its own project name and persistent directory.
2. Prefer official images and vendor docs. **Pin tested versions** rather than using `latest`; document upgrade compatibility.
3. Prefer a **self-hosted GitHub runner on the target host**; otherwise use a secured, existing SSH deployment path. Never assume a runner runs on the target host.
4. Separate cloud/local roles when topology differs (e.g. hub in cloud, agent on premises). Avoid duplicating control planes and unnecessary components.
5. Favor minimal operational overhead: only required containers, native health checks, log rotation, appropriate restart policy, and no unnecessary database/proxy/exporter.
6. Use dedicated Docker networks and restrict published ports. Bind admin UIs to loopback or a secured reverse proxy; do not expose sensitive ports by default.
7. For host-level Docker monitoring, explicitly review Docker socket privilege and limit access where practical.

## Repository layout

Follow established layout first. If absent, use:

```text
infra/<service>/
  compose.yaml                # or compose.<target>.yaml for divergent hosts
  .env.example                 # variable names and safe example values only
  README.md                    # runbook, bootstrap, verification, rollback
.github/workflows/
  deploy-<service>.yml
```

Do not commit `.env`, secrets, tokens, SSH private keys, or generated credentials. Add applicable entries to `.gitignore`.

## Configuration contract: GitHub Environments

- Use **GitHub Environment Variables** (`vars.*`) for non-sensitive deployment settings (image tag, host label, deployment path, public URL, published port, feature flags).
- Use **GitHub Environment Secrets** (`secrets.*`) for passwords, private keys, tokens, connection strings, and other sensitive values.
- Use an explicit job `environment: <environment-name>` so deployment receives the correct per-target configuration, approvals, and protection rules.
- Map GitHub values to Compose `${VAR:?required}` inputs via scoped workflow `env:` or a temporary, permission-restricted env file. Never echo the file or print secrets.
- Do not assume secrets are accessible to pull requests from forks. Restrict deployments to trusted refs or manual invocation.
- Keep the same variable names across targets where possible; configure different values per GitHub Environment.
- If credentials are created by the service after startup, document a **two-phase bootstrap**: start control plane, generate agent credentials, add GitHub Secrets, then deploy agents.

### Suggested naming

| GitHub Environment Variable | Meaning |
|---|---|
| `DEPLOY_PATH` | Persistent target-side project directory |
| `SERVICE_IMAGE` | Official repository/name image |
| `SERVICE_VERSION` | Pinned tested image tag |
| `SERVICE_PUBLIC_URL` | External URL when needed |
| `SERVICE_PORT` | Host-published port, if needed |

Add service-specific names only when needed (e.g. `HUB_URL`, `GPU_ENABLED`). Put sensitive keys in GitHub Secrets with descriptive names. **Do not hardcode host paths, addresses, or credentials in reusable workflows.**

## Docker Compose implementation

For each service:

- Use the documented image and environment variables; validate compatibility with the chosen release.
- Use a deterministic Compose project name and named/bind volumes for *all* persistent data. Keep persistent data outside ephemeral CI workspaces.
- Specify `restart: unless-stopped` unless vendor requirements indicate otherwise.
- Configure bounded log rotation (e.g. `json-file` with `max-size`/`max-file`) in accordance with host logging policy.
- Add a **real application health check** only if a documented, available health endpoint/command exists; never call a container healthy merely because the process exists.
- Expose only required ports; keep databases and administration endpoints private.
- Select least privileges, avoid `privileged: true`, and document any necessary Docker socket or GPU access.
- Set memory/CPU limits only after verifying supported baseline requirements; avoid limits likely to cause OOM/restart loops.
- Do not deploy unnecessary monitoring/notification services if the application already provides them.
- Use `${VAR:?required}` for mandatory Compose variables and provide `.env.example` with no real secrets.

## GitHub Actions workflow

Use the repository's working runner/SSH deployment pattern. The workflow should:

1. Trigger on `workflow_dispatch` and optionally trusted branch changes in relevant directories; guard the deploy job from untrusted PRs.
2. Set minimal `permissions: contents: read` and the correct `environment:` for target-specific `vars`/`secrets`.
3. Use `concurrency` per service **and target** to avoid concurrent deployments.
4. Check out the pinned commit being deployed (where relevant).
5. Verify Docker and Compose prerequisites, required variables, target path, disk free space, and essential mounted dependencies.
6. Transfer or stage **only deployment artifacts** to the target's persistent deployment directory (never prune or delete app data).
7. Render runtime configuration securely; fail fast if required values are missing; do not log secrets.
8. Run `docker compose -f <file> config --quiet` to validate configuration before changing running services.
9. Pull pinned images and run targeted `docker compose -p <project> -f <file> up -d --remove-orphans` for **this project only**. Use `--remove-orphans` only with the confirmed dedicated Compose project.
10. Verify readiness with `docker compose ps`, documented service health checks, and a bounded retry loop. Check the public endpoint separately when appropriate.
11. Report the deployed image version, commit, service health, and diagnostic commands without leaking environment values.
12. On failure, preserve logs for debugging and provide the **documented rollback**. Do not claim an automatic rollback unless implemented and tested.

**Never** use unscoped `docker system prune`, delete unrelated volumes, restart unrelated containers, or execute destructive cleanup as part of routine deployment.

## Multi-host deployment

- Use separate GitHub Environments and deployment jobs for hosts with different configuration or roles (e.g. `production-aws`, `production-local`).
- Bind each job to verified target-specific runner labels or a known SSH route. Validate that labels actually select the intended machine.
- Keep shared Compose configuration only when genuinely shared; prefer small explicit overrides for differences such as GPU access.
- For cross-host agents, prefer authenticated outbound connections where supported. Document firewall, DNS, TLS, reverse-proxy/WebSocket, and certificate requirements.
- Deploy dependencies/control plane before agents. Require explicit verification before moving to dependent hosts when needed.

## Verification and rollback

After deploy, verify:

- `docker compose ps` shows expected state, and readiness endpoint passes.
- Restart and recreation preserve volumes and data.
- Required ports, inter-service connections, and external access work.
- Alerts/notifications work if the service offers them.
- Service comes back after host reboot (`restart` policy).
- `docker stats --no-stream` and `docker system df` show acceptable resource usage.
- Existing unrelated containers and networks were not disrupted.

For rollback, retain last-known-good image tag, Compose config, and relevant schema/upgrade notes. Revert via the same workflow if compatible; **database/schema downgrades may need restore from backup**, not just an older image. Include backup/restore instructions when stateful.

## Deliverables

Produce the actual implementation, when repository access permits:

1. Service-specific Docker Compose file(s).
2. GitHub Actions deployment workflow(s) using GitHub Environments.
3. `.env.example` and a GitHub **Variables vs Secrets** table.
4. Short README with topology, first-time bootstrap, prerequisites, deploy, health checks, notifications if applicable, upgrades, and rollback.
5. Evidence of checks performed and an explicit list of tests blocked by unavailable infrastructure/access.

## Definition of done

A deployment is complete only when it is reproducible, target-scoped, secret-safe, persistent, health-checked, rollback-documented, resource-conscious, and does **not** modify unrelated services. Distinguish locally validated configuration from a successfully executed remote deployment.
