# Build backend candidates from source

Build both the Python dependency base and application from this checkout. The
supported path does not use an upstream prebuilt server image. These instructions
prepare candidate artifacts; they do not authorize a deployment or a paid call.

## Inputs and open release gates

Use a dedicated builder with direct access to reviewed registries. Do not change
the running host's registry settings or reuse its private configuration. Docker
daemon registry mirrors and network proxies live outside these Dockerfiles;
verify that the dedicated builder has neither. Enforce and capture build egress
outside the build process. A source URL check alone cannot prove that boundary.

Supply full `@sha256` identities from Docker Hub for these repositories:

| Input | Reviewed repository | Compatibility to verify |
| --- | --- | --- |
| `PYTHON_IMAGE` | `docker.io/library/python` | Python 3.10, Debian slim with apt |
| `NODE_IMAGE` | `docker.io/library/node` | Node 20, Linux build tools |
| `MAVEN_IMAGE` | `docker.io/library/maven` | Maven 3.9, JDK 21 |
| `RUNTIME_IMAGE` | `docker.io/bellsoft/liberica-runtime-container` | JRE 21 glibc image with apk |
| `MYSQL_IMAGE` | `docker.io/library/mysql` | MySQL compatible with the existing database |
| `REDIS_IMAGE` | `docker.io/library/redis` | Redis compatible with the application |

The operator supplied this Python candidate input for the separate fresh voice
build: `docker.io/library/python:3.10-slim-bookworm@sha256:5be5aaecb962a41567bc8041f1e9e3432cb085b037fe057f9a562630b2e4b370`.
Pass it explicitly as `PYTHON_IMAGE`. Other image identities remain unselected.
Do not substitute `latest`. Image syntax validation checks repository and digest
shape; it does not verify image contents, platform support, or licenses.

Python uses official PyPI (`pypi.org`, artifact delivery through
`files.pythonhosted.org`) with TLS verification and no trusted-host shortcut.
The Java build copies the checked-in `.mvn` settings, including the Maven Central
override for transitive repositories. GHCR is the optional owned image output.

The frontend lockfile still needs its owner's review/migration from
`registry.npmmirror.com`. `--registry` alone does not replace lockfile `resolved`
URLs. The offline guard rejects those URLs before installation. Official npm
(`https://registry.npmjs.org`) also requires explicit operator approval; set
`NPM_REGISTRY` to that exact value only after review. There is no mirror fallback.
Do not regenerate the lock against a new registry as part of an unrelated build.

Further unresolved inputs prevent a pinned/reproducible-build claim:

- The main-owned `main/xiaozhi-server/requirements.lock` records transitive package
  versions/artifact hashes resolved for CPython 3.10 Linux aarch64 through official
  PyPI. The base installs that lock with `--require-hashes --only-binary=:all:`;
  unavailable wheels fail instead of fetching unlocked source-build dependencies.
  Verify x86_64 and other platform coverage separately. The base also records
  `/opt/python-install-report.json` and `/opt/python-installed.txt` after install.
- apt/apk package versions and repository snapshots remain unpinned. Maven
  plugin/transitive resolution and npm lifecycle-script downloads need fresh-cache
  verification. The Dockerfiles do not enforce a network allowlist themselves.
  Exact OS package-registry origins depend on the as-yet unselected image digests;
  inspect and approve those repositories before a networked build. Dockerfile
  stages clear standard proxy variables; that does not audit daemon-side mirrors,
  package-manager configuration, redirects or build-script subprocesses.
- CI actions use major-version tags; Buildx/BuildKit helper images are not pinned.
  CI-only pytest tooling also remains outside the application hash lock. Resolve
  those identities and record full artifact SBOMs before release.
- Silero VAD uses the checked-in ONNX file at
  `main/xiaozhi-server/models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx`.
  The source report hashes its bytes. Provenance/license review and a pinned model
  manifest remain release gates. The default configuration requires the operator
  to provision its VAD model path; this byte hash does not make that configuration
  ready. No ASR model download is part of these builds.

## Offline checks

From the repository root, with reviewed image values supplied in your shell:

```sh
python3 tools/build-inputs.py images --python-image "$PYTHON_IMAGE" \
  --node-image "$NODE_IMAGE" --maven-image "$MAVEN_IMAGE" \
  --runtime-image "$RUNTIME_IMAGE"
node tools/build-npm-lock.mjs main/manager-web/package-lock.json
python3 tools/build-inputs.py report
python3 tools/build-policy-tests.py
node --test tools/build-npm-lock.test.mjs
```

The source report reads a fixed list of public build manifests and the VAD model.
It does not inspect private configuration. Save its JSON with your candidate
record; it is a source-input inventory, not an installed dependency SBOM.

## Candidate builds

Run these only in an approved dedicated build environment after the input gates
pass. Use unique local tags that cannot overwrite rollback artifacts. These
commands build images; none starts, stops, or replaces a service.

```sh
docker build --no-cache --pull -f Dockerfile-server-base \
  --build-arg PYTHON_IMAGE="$PYTHON_IMAGE" \
  -t xiaozhi-local/server-base:candidate .
docker build --no-cache -f Dockerfile-server \
  --build-arg SERVER_BASE_IMAGE=xiaozhi-local/server-base:candidate \
  -t xiaozhi-local/server:candidate .
docker build --no-cache --pull -f Dockerfile-web \
  --build-arg NODE_IMAGE="$NODE_IMAGE" --build-arg MAVEN_IMAGE="$MAVEN_IMAGE" \
  --build-arg RUNTIME_IMAGE="$RUNTIME_IMAGE" --build-arg NPM_REGISTRY="$NPM_REGISTRY" \
  -t xiaozhi-local/web:candidate .
```

The base tag above identifies an image you just built locally. Inspect and record
its image ID before building the server; use a unique tag per attempt. For remote
builders, publish your source-built base to your owned GHCR repository and pass
its resulting digest as `SERVER_BASE_IMAGE`. Do not pass an upstream server base.

The web build excludes `.env` files from its context. It supplies non-secret
`VUE_APP_API_BASE_URL=/xiaozhi` and `VUE_APP_PUBLIC_PATH=/`, and disables optional
frontend CDN loading. Override public build arguments only after review. Never
pass provider keys or the management authentication secret as build arguments.

The CI image workflow builds a new base from the same checkout, passes that
owned output digest to the server build, and records output image digests.
Repository variables supply the reviewed inputs above. Missing inputs fail;
there is no default upstream artifact. CI provenance and source hashes alone do
not satisfy the remaining lock, SBOM, egress, or runtime acceptance gates.

## Rehearsal and rollback

Use the [server-only](Deployment.md) or [full-module](Deployment_all.md) candidate
configuration. Keep the Compose files in their checkout location so `../..` stays
the build context. Supply a new Compose project name, separate storage, and spare
loopback ports. Do not reuse the parent wrapper's files or live volumes.

Before any later cutover, verify a restorable backup of the database, uploads,
audio/history, Redis-dependent state, private configuration and old image digests.
Rehearse migrations on disposable copies; preserve executed SQL checksums. Record
DNS/outbound attempts for startup, accounts, direct WS turns, history and removed
features. Gateway transport testing needs separate authorized wrapper/gateway
coordination. Deterministic local AI fixtures do not prove real-provider accuracy.

Get explicit approval before promotion, a real-provider trial, or a restart.
Rollback must restore compatible application artifacts and data together, while
preserving post-cutover writes separately. Keep removed-service egress blocked:
restoring old artifacts does not authorize old provider credentials or routes.
