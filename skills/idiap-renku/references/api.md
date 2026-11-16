# Renku data-services API cheat-sheet

Base: `$RENKU_URL/api/data` (live OpenAPI spec: `/api/data/spec.json`, UI: `/swagger`).
All calls below go through `scripts/renku_api.py METHOD /path [json|@file]`.
IDs are ULIDs (strings) except resource classes/pools (integers).

`PATCH` on `/projects/{id}`, `/data_connectors/{id}` and `/session_secret_slots/{id}`
needs `--if-match <etag>`; take `etag` from a `GET` of the same object.

## Discovery

| Call | Use |
|---|---|
| `GET /user` | your `id` (Keycloak), `username`; your namespace slug is `username` |
| `GET /namespaces` / `GET /groups` | namespaces you can create projects in |
| `GET /resource_pools` | pools and classes you may use (authenticated sees more) |
| `GET /environments` | global environments (ids for `{"id": ...}` launchers) |
| `GET /oauth2/connections` | is the GitLab/GitHub integration connected (`status`)? |
| `GET /storage_schema` | rclone backends and their option names |
| `GET /repository?url=<git-url>` | can Renku (and you) read/write that repo? |
| `GET /search/query?q=<text>` | search projects, groups, users, data connectors |

## Projects, groups, members

```jsonc
// POST /groups
{"name": "My Group", "slug": "my-group", "description": "..."}
// POST /projects   (namespace = user or group slug)
{"name": "My project", "namespace": "my-group", "slug": "my-project",
 "visibility": "private", "description": "...",
 "repositories": ["https://gitlab.example.org/ns/repo.git"]}
// GET  /namespaces/{namespace}/projects/{slug}     -> project (id, etag)
// PATCH /projects/{id} --if-match <etag>           e.g. {"repositories": [...]}
// PATCH /projects/{id}/members  (adds or changes roles: viewer|editor|owner)
[{"id": "<keycloak-user-id>", "role": "editor"}]
// PATCH /groups/{slug}/members  same shape
// DELETE /projects/{id}/members/{user_id}
```

Find a user id with `GET /search/query?q=type:user <name>` or `GET /users?exact_email=...`.

## Session and job launchers

`launcher_type`: `interactive` (session), `non-interactive` (job, needs a command),
`app` (public projects only). `resource_class_id` comes from `GET /resource_pools`.

Global environment:

```json
{"project_id": "<pid>", "name": "Python", "launcher_type": "interactive",
 "resource_class_id": 3, "environment": {"id": "<global-env-id>"}}
```

External image:

```json
{"project_id": "<pid>", "name": "My image", "launcher_type": "interactive",
 "resource_class_id": 3, "disk_storage": 5,
 "environment": {"environment_kind": "CUSTOM", "environment_image_source": "image",
   "name": "my-image", "container_image": "registry.example.org/ns/img:latest",
   "default_url": "/", "port": 8888, "uid": 1000, "gid": 1000,
   "working_directory": "/home/renku/work", "mount_directory": "/home/renku/work"}}
```

Built from a code repository (Renku buildpacks):

```json
{"project_id": "<pid>", "name": "From code", "launcher_type": "interactive",
 "resource_class_id": 3,
 "environment": {"environment_image_source": "build",
   "repository": "https://gitlab.example.org/ns/repo.git",
   "builder_variant": "python", "frontend_variant": "vscodium",
   "repository_revision": "main", "context_dir": "."}}
```

- `builder_variant`: `python` (detects pixi.toml / `[tool.pixi]` in pyproject.toml,
  uv, poetry, environment.yml, requirements.txt) or `r` (renv).
- `frontend_variant`: `vscodium`, `jupyterlab`, `ttyd` (web terminal), `rstudio` (R),
  `ssh` (only if the instance runs an SSH proxy), `none`, `infer`.
- `none` failed with Idiap's buildpacks 0.12.3 for the python builder ("No buildpack
  groups passed detection"); only R groups accept it.
- `repository_revision` and `context_dir` are optional.
- Job launcher: same, with `"launcher_type": "non-interactive"` and a regular frontend
  (for example `vscodium`, so the image matches the interactive one), plus
  `"command": ["bash", "-lc"]` and `"args": ["<shell line>"]` inside `environment`. The
  command replaces the frontend when the job runs.

Launcher maintenance:

```jsonc
// GET   /projects/{pid}/session_launchers
// PATCH /session_launchers/{lid}  {"resource_class_id": 2}
//   built env: {"environment": {"build_parameters": {"frontend_variant": "vscodium"}}}
//   (then POST /environments/{eid}/builds to rebuild)
// GET   /session_launchers/{lid}/data_connectors     (which links it mounts)
// PATCH /session_launchers/{lid}/data_connectors
[{"data_connector_link_id": "<link-id>", "policy": "read_only"}]   // excluded|read_only|read_write
// PATCH /session_launchers/{lid}/secrets
[{"secret_slot_id": "<slot-id>", "policy": "included"}]            // excluded|included
```

## Image builds

The environment id is `launcher.environment.id`.

```text
POST  /environments/{eid}/builds          (no body)  -> build {id, status}
GET   /environments/{eid}/builds          list (latest first)
GET   /builds/{bid}                       status: in_progress|failed|cancelled|succeeded
GET   /builds/{bid}/logs                  build log (text/JSON)
PATCH /builds/{bid}  {"status": "cancelled"}
```

## Data connectors

SFTP (`storage.configuration` keys follow rclone, see `GET /storage_schema`):

```json
{"name": "Group data", "namespace": "my-group", "slug": "group-data",
 "visibility": "private",
 "storage": {"configuration": {"type": "sftp", "host": "login.example.org",
                               "port": "22", "user": "<username>"},
             "source_path": "/path/on/server", "target_path": "group-data",
             "readonly": true}}
```

- `POST /data_connectors` creates it. Leave secrets (`key_pem`, `pass`) **out** of
  the configuration and store them per user instead:
  `PATCH /data_connectors/{dcid}/secrets` with `[{"name": "key_pem", "value": "<pem with \n>"}]`.
- `POST /data_connectors/{dcid}/project_links` with `{"project_id": "<pid>"}` links it.
  The link id comes back; it is also listed by `GET /projects/{pid}/data_connector_links`.
- Mount point is `$RENKU_MOUNT_DIR/<target_path>` (usually `/home/renku/work/<target_path>`).
- Other backends: `s3`, `webdav`, `doi` (Zenodo/Dataverse, `{"type": "doi", "doi": "10.5281/..."}`),
  `polybox`/`switchDrive`, `azureblob`...

## Secrets in sessions

Project slot (file name inside `/secrets` or the project's `secrets_mount_directory`):

```jsonc
// POST /session_secret_slots
{"project_id": "<pid>", "name": "API token", "filename": "api_token"}
// each user fills the slot with their own value:
// PATCH /projects/{pid}/session_secrets
[{"secret_slot_id": "<slot-id>", "value": "<secret>"}]
// or reuse an existing user secret: [{"secret_slot_id": "...", "secret_id": "<user-secret-id>"}]
// user secrets: POST /user/secrets {"name": "...", "value": "...", "kind": "general"}
```

## Sessions and jobs

```jsonc
// POST /sessions
{"launcher_id": "<lid>"}
// jobs: add "submission_id" (unique per launcher, ^[a-z][a-z0-9-]{3,}),
//       "job_command_override": ["bash","-lc"], "job_args_override": ["..."]
// optional on both: "resource_class_id", "disk_storage",
//   "env_variable_overrides": [{"name": "X", "value": "1"}],
//   "data_connectors_overrides": [{"data_connector_id": "<dcid>", "skip": true}]
// GET    /sessions                       yours; .status.state, .url, .launcher_id
// GET    /sessions/{name}                state: starting|running|hibernated|failed|succeeded|stopping
// GET    /sessions/{name}/logs?max_lines=500
// PATCH  /sessions/{name} {"state": "hibernated"} | {"state": "running"} | {"resource_class_id": 2}
// DELETE /sessions/{name}                stop and delete (unsaved, unpushed work is lost)
// GET    /persisted_logs/sessions/{lid}/runs   history of past runs (incl. finished jobs)
```

Interactive sessions get a browser URL (`url`). Jobs end in `succeeded` or `failed`.
Their logs stay readable until the job is removed, which is usually 24 h after it ends.
