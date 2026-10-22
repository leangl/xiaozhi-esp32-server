# Frontend translation verification

Executed on 2026-10-20 with Node 22.22.3 against baseline
`eb9dc8ca0fc8a30bc8afb0f302dcfc1578f76a7b` and isolated translated source copies.
No repository source, package manifests or lockfiles changed during validation.
Dependency downloads used official npm only, without account credentials.

## Web console

Both source trees give the same results:

- Full Vitest suite: **53/53 pass in UTC**. In Buenos Aires time, **52 pass and
  one existing date assertion fails** (`tests/date.test.mjs:83`, expecting
  `2026-09-02`, receiving `2026-09-01`). The local-timezone failure is retained,
  not concealed by the successful diagnostic UTC run.
- Production builds: **pass**, with the same four warning categories.
- Separate Node snapshot/API/translation contract tests: **27 passed** on the
  translated source (22 original checks and five new translation checks).

Dependencies were installed with:

```sh
npm ci --registry=https://registry.npmjs.org/ \
  --replace-registry-host=always --ignore-scripts --no-audit --no-fund
```

Installation used an empty temporary HOME/config/cache; all 2,254 HTTP log
records referenced `registry.npmjs.org`. The replace-registry flag is necessary
because the unchanged lock contains mirror URLs. All lifecycle scripts remained
disabled except one individually reviewed dependency initialization:
`node scripts/postinstall.cjs` from `node_modules/v-code-diff`.
Its complete script and helper were inspected before execution; they only copy
the package's version-specific Vue entry files to its root `dist` entries.
The initial script-free build could not resolve that missing entry; this was a
setup prerequisite, not a broken product build. No further hooks were needed.

The normal package commands were run in each temporary copy:

```sh
TZ=America/Argentina/Buenos_Aires npm run test:unit
TZ=UTC npm run test:unit
npm run build
```

The source/lock preservation checks passed after the successful builds. Build
outputs are not claimed byte-identical: diagnostic prose was intentionally
translated and bundle content hashes may therefore change.

## Mobile console

Both source trees give the same results using pnpm **10.10.0**:

- H5 production builds: **pass** with `CHOKIDAR_USEPOLLING=1` to avoid the shared
  host `EMFILE` watcher limit.
- `vue-tsc --noEmit`: **pass after build-generated declarations**.
- A fresh-copy type-check before the build reports the same 42 missing
  auto-import names on both versions. The build produces identical
  `src/types/auto-import.d.ts` files and resolves these diagnostics. This is not
  a claim that type-check succeeds before its existing generation prerequisite.
- Separate Node snapshot/voice/device tests: **20 passed**.

The official registry, a temporary Corepack cache/store, frozen lockfile and
`--ignore-scripts` were used. Temporary-only `.npmrc` settings replaced the
registry and disabled scripts. Temporary-only `supportedArchitectures` settings
retained both Darwin arm64/x64 packages already declared by the project; no
dependencies or lock entries were removed.

```sh
corepack pnpm@10.10.0 install --frozen-lockfile --ignore-scripts \
  --registry=https://registry.npmjs.org/ --store-dir=/temporary/store
CHOKIDAR_USEPOLLING=1 corepack pnpm@10.10.0 exec uni build
corepack pnpm@10.10.0 exec vue-tsc --noEmit
```

No `prepare`/`preinstall`, Git initialization, Husky, DCloud login, native build,
signing, application server, provider request or deployment was performed.
These results validate H5 and types, not Android/iOS native packaging or device
runtime integration. Framework/provider removal remains separately pending.
