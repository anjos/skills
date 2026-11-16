---
name: idiap-renku
description: Create, maintain and drive projects on Idiap's Renku 2.0 instance (renku.idiap.ch) from an agent, through its REST API and the rnk CLI. Use when asked to set up a Renku project, link GitLab repositories, build session or job environments, mount Idiap storage via data connectors, manage secrets or members, start/stop sessions, submit jobs, or read their logs on renku.idiap.ch (or another Renku 2.0 deployment).
---

# Renku @ Idiap

[Renku](https://docs.renkulab.io/en/latest/docs/users/) connects code, data and
compute in a **project**:

- **Code repositories**: git URLs. They are cloned into every session and job.
- **Data connectors**: rclone-based remote storage, mounted read-only or read-write.
- **Launchers**: an *environment* (a container image) plus a *resource class*
  (CPU/RAM/GPU/disk).
  - `interactive` launchers start browser **sessions** (VSCodium, JupyterLab, ttyd,
    RStudio).
  - `non-interactive` launchers run **jobs**: one command, with logs.
- **Secrets**: per-user values, mounted as files in `/secrets`.
- **Members**: users and groups with viewer, editor or owner roles.

Idiap's instance is <https://renku.idiap.ch>. You log in with Idiap credentials, and
it is tightly coupled to <https://gitlab.idiap.ch>.

## Tools

- **`scripts/renku_api.py`** (stdlib Python, no install) is the main tool.
  - Covers the **whole** data-services API: projects, launchers, builds, data
    connectors, secrets, members, sessions and jobs.
  - Endpoints and payloads: [references/api.md](references/api.md). The live spec is at
    `https://renku.idiap.ch/api/data/spec.json` and is authoritative if the two
    disagree.

  ```sh
  R() { python3 -I <skill-dir>/scripts/renku_api.py "$@"; }   # bash and zsh
  $R login            # prints a URL + code; the user approves in a browser (once per ~day)
  $R GET /user
  $R POST /projects @project.json
  ```

  - Tokens are cached at `~/.cache/renku-api/<host>.json` (0600) and refresh
    automatically.
  - When the refresh token expires, re-run `login`. Run it in the background, show the
    printed URL to the user, and wait.
  - `RENKU_URL` selects another instance, for example `https://renkulab.io`.
- **`rnk`** ([CLI reference](https://docs.renkulab.io/en/latest/docs/users/cli/cli-reference/))
  is optional. It is convenient for `rnk job start --launcher <id> --wait`, `rnk
  session logs -f` and `rnk clone`. It **cannot** create projects, launchers, data
  connectors or secrets.
  - Install with `curl -sfSL https://raw.githubusercontent.com/SwissDataScienceCenter/renku-cli/main/install.sh | bash`.
  - Point it at Idiap with `export RENKU_CLI_RENKU_URL=https://renku.idiap.ch`, then
    run `rnk login`.
  - Use `--format json` for parseable output.
- **`glab`** reads and edits the GitLab side (repos, CI, container registry).

## Idiap specifics

Some of this was checked against the live instance (2026-11) and some comes from
Idiap's internal docs (`www/documentation` → `docs/renku/`), which can lag. **Probe
before relying on anything:**

```sh
$R GET /resource_pools        # the classes *you* can use (anonymous sees only `default`)
$R GET /environments          # global images
$R GET /oauth2/connections    # GitLab integration connected?
$R GET /storage_schema        # available rclone backends
```

- **Compute.**
  - The public pool `default` is shared with external partners. Its classes are
    small (0.5 CPU, 1 GB), medium (1 CPU, 2 GB) and large (2 CPU, 4 GB), with 5 GB
    disk at most.
  - Idiap's docs describe an *Internal* pool (staff only) with `large-cpu` (4 CPU,
    8 GB) and `large-gpu` (4 CPU, 8 GB, 1 GPU), with 10 GB disk. The GPUs are H100 in
    MIG mode, so each GPU is a slice of an H100.
  - Resources are limited: always pick the **smallest** class that works.
  - Sessions hibernate after idling. Stop sessions when you are done.
  - Large batch work (TB-scale preprocessing, multi-GPU training) still belongs on the
    Slurm grid; the Renku-Slurm integration is announced but not live.
- **Global environments**: Python/Jupyter (`/lab`) and RStudio. Their working and mount
  directory is `/home/jovyan/work`. Job launchers cannot use global environments.
- **Images built by Renku** go to `acp-registry.idiap.ch/renku/`.
  - Builds use SDSC's [frontend buildpacks](https://github.com/SwissDataScienceCenter/renku-frontend-buildpacks).
    They detect **pixi** (`pixi.toml` or `[tool.pixi]`), uv, poetry, conda
    `environment.yml`, `requirements.txt` and `renv.lock`.
  - Upstream Renku can build from **private** repos (since 2.18), but only when the
    user's GitLab integration is connected. Idiap's docs predate this and recommend
    a CI template instead (see Fallbacks).
  - In buildpack images, the working and mount directory is `/home/renku/work`.
- **GitLab integration.** The user connects *GitLab - Idiap* once, under Profile →
  Integrations. Without it, private repos can't be cloned or built, and sessions
  can't push.
  - Adding someone to a Renku project does **not** give them access to its repository.
    They need GitLab access in their own name.
- **Data.**
  - Idiap storage (`/idiap/user/<u>`, `/idiap/project/<p>`, `/idiap/group/<g>`,
    `/idiap/temp/<u>`, `/idiap/resource/database/...`) is reached through
    **SFTP data connectors** to `login.idiap.ch`, using a dedicated key pair.
  - Through SFTP, file-system ACLs apply as the user.
  - SFTP mounts are fine for configs, small databases and outputs, but slow for
    TB-scale, high-IOPS reads.
  - No NFS backend is offered. S3 is announced. "Project storage" (in-cluster volumes)
    needs admin enablement.
- **Secrets.** Idiap uses a low-trust model: never commit credentials. Use secret slots
  and per-user values, which are mounted under `/secrets`, and data connector secrets.
- **Visibility.** Keep projects private. Public projects are visible to anonymous users
  and need **supervisor approval** at Idiap.
- **Not available or unverified.** An SSH proxy into sessions exists upstream but was
  not found on renku.idiap.ch. Agents therefore cannot type into an interactive
  session; use a **job** to run commands non-interactively and read its logs.
  - Coding agents inside images (Claude/Codex/Pi) need a `project.toml` in the built
    repo:

    ```toml
    [_]
    schema-version = "0.2"

    [[io.buildpacks.build.env]]
    name = "BP_RENKU_AI_AGENTS"
    value = "claude"
    ```

## Recipes

Each recipe is a sequence of `$R` calls; payloads are in [references/api.md](references/api.md).
Capture the ids from each response for the next call.

1. **Orient**: `GET /user` gives the user's `id` and `username`. The username is the
   personal namespace. `GET /groups` lists group namespaces. Run the probes above.
2. **Project**:
   - `GET /namespaces/<ns>/projects/<slug>` first, so you never create a duplicate.
   - Otherwise `POST /projects` with `visibility: private` and the repo's **https**
     clone URL in `repositories`.
   - Check access with `GET /repository?url=<https-url>`.
3. **Group** (if asked): `POST /groups`, then `PATCH /groups/<slug>/members`.
4. **Environment and launcher**: pick the first option that works.
   1. Global environment: `{"environment": {"id": ...}}`. Interactive only.
   2. Build from the repo (`environment_image_source: build`). The response's
      `environment.id` gives the build endpoints:
      - Creating the launcher starts the first build automatically: find it with
        `GET /environments/<eid>/builds`. `POST /environments/<eid>/builds`
        rebuilds, for example after the repo changes.
      - Poll `GET /builds/<bid>` every 30–60 s.
      - On failure, read `GET /builds/<bid>/logs`.
   3. External image (`environment_image_source: image`), for example one built by
      GitLab CI.
5. **Job launcher** (to run things headless):
   - Same build parameters, with `launcher_type: non-interactive`,
     `command: ["bash","-lc"]` and `args: ["<commands>"]`.
   - Keep a real `frontend_variant` such as `vscodium`. `none` fails buildpack detection
     for python builds on Idiap.
   - The project's repos are cloned under the working directory, so `cd` into
     `<repo-name>` first.
   - With pixi images, call tools through `pixi run`.
6. **Data connector**:
   - `POST /data_connectors` with no secret fields, then
     `PATCH /data_connectors/<id>/secrets` with the user's `key_pem`.
   - Link it with `POST /data_connectors/<id>/project_links`.
   - Set the policy per launcher with `PATCH /session_launchers/<lid>/data_connectors`.
   - It mounts at `$RENKU_MOUNT_DIR/<target_path>`.
7. **Config files and credentials**:
   - `POST /session_secret_slots` with a `filename`; each user fills it via
     `PATCH /projects/<pid>/session_secrets`.
   - Enable it per launcher with `PATCH /session_launchers/<lid>/secrets`.
   - The file appears at `/secrets/<filename>`.
8. **Run**:
   - Interactive: `POST /sessions {"launcher_id"}`, poll `GET /sessions/<name>` until
     `running`, then hand the user `url`.
   - Job: `POST /sessions` with `submission_id` (plus optional command/args overrides),
     poll until `succeeded`/`failed`, then `GET /sessions/<name>/logs`.
   - Stop with `DELETE /sessions/<name>`.
9. **Members**: `PATCH /projects/<pid>/members [{"id","role"}]`. Find user ids with
   `GET /users?exact_email=<email>` or `GET /search/query?q=<name>`. Remind the user
   that collaborators also need repository and storage access.

### SFTP key for Idiap storage (once per user)

```sh
ssh-keygen -t rsa -b 4096 -m PEM -N '' -f ~/.ssh/id_rsa_renku     # dedicated, Renku only
ssh-copy-id -i ~/.ssh/id_rsa_renku.pub "$USER@login.idiap.ch"
# rclone wants the PEM on one line, newlines written as a literal backslash-n
(umask 077; python3 -c 'import json,pathlib,sys;print(json.dumps([{"name":"key_pem","value":pathlib.Path(sys.argv[1]).read_text().strip().replace("\n","\\n")}]))' \
  ~/.ssh/id_rsa_renku > ~/.cache/renku-api/dc-secret.json)
$R PATCH /data_connectors/<dcid>/secrets @$HOME/.cache/renku-api/dc-secret.json; rm ~/.cache/renku-api/dc-secret.json
```

Ask before generating keys or touching `authorized_keys`.

## Patterns

**Collaborative document (LaTeX/Markdown with a pixi toolchain)**
- Project: one repo.
- Launcher: build from code, python builder, `vscodium` frontend, smallest class.
- Job launcher: `cd <repo> && pixi run <build-task>`. This lets the agent check that the
  document compiles and inspect logs (page counts, warnings) without a browser.
- Each collaborator runs their own session and syncs through git. Renku has no
  real-time co-editing; keep an Overleaf bridge if the repo has one.

**GPU ML package with institutional data**
- Project: the package repo, plus read-only SFTP connectors for each raw or derived
  dataset directory, plus one read-write connector for outputs (for example under
  `/idiap/temp/<user>`). Jobs keep nothing after they end.
- Put the tool's config file (data paths pointing at `$RENKU_MOUNT_DIR/<target>`) in a
  secret slot, and copy it into place at the start of the job command.
- Launchers: interactive (`vscodium`) and non-interactive, on the GPU class.
- A pixi project's **default** environment is what gets baked. If CUDA lives in a
  non-default pixi environment, you need one of:
  - a `project.toml` with `BP_PIXI_ENVIRONMENT_NAME`;
  - `pixi install -e <env>` at start (watch the disk limit);
  - an external image built by CI.

## Fallbacks

- **Private repo build fails** (auth or clone errors in the build logs):
  1. Confirm `GET /oauth2/connections` shows GitLab connected and `GET /repository`
     sees the repo.
  2. Otherwise build the image in GitLab CI with Idiap's template. This needs
     the project's container registry enabled and runners tagged `linux`/`docker`.
     Then use the resulting `docker.idiap.ch/<ns>/<repo>:latest` as an external image
     with working and mount directory `/home/renku/work`.

     ```yaml
     include:
       - project: 'aip/iaip_build_helpers'
         ref: main
         file: '/templates/renku-image.gitlab-ci.yml'
     stages: [build]
     variables:
       RENKU_FRONTEND: "vscodium"   # vscodium | jupyterlab | ttyd | rstudio
     ```

- **Buildpacks don't detect the toolchain**: use the global Python environment and
  bootstrap the tool in the job command (for example `curl -fsSL https://pixi.sh/install.sh | bash`).
- **Session stuck `starting` or `failed`**: read `GET /sessions/<name>/logs`, then
  `.status.message`. Common causes are a full disk (raise `disk_storage` within the
  class maximum), missing data connector secrets, or an exhausted pool quota.

## Rules

- Before creating, changing, sharing or deleting anything on the platform, state what
  will happen and get the user's go-ahead. That includes launching GPU sessions and
  adding members.
- Never put secrets in repos, launcher env vars, or chat output. Pass them through
  files and remove those files afterwards.
- Look up before you create, so the recipes stay safe to re-run.
- Report the platform's actual responses. Never claim a build, job or session succeeded
  without seeing its status.
