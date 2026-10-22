# Provider benchmark status

The legacy interactive benchmark is unavailable in the supported profile. Its
streaming tests imported removed vendor SDKs/adapters and called vendor-specific
protocols outside the retained provider seam. The generic runners also swept
configured offerings and could trigger real calls while discovering benchmarks.
They do not establish performance for the retained profile.

`main/xiaozhi-server/performance_tester.py` now prints an unavailable explanation
and exits with status 2. It loads no private configuration, imports no provider,
downloads no model and makes no network request. The obsolete test modules are
removed. Application HTTP, WebSocket and provider interfaces are unchanged by
this retirement. Historical published results do not certify this configuration.

A future benchmark needs a separate explicit request: select one supported
provider, validate its endpoint through the shared policy, provide synthetic
input, disable environment proxies/redirect fallback, and define timing and cost
limits. Start with deterministic local fixtures. Cloud accuracy/latency testing
requires approval, explicit credentials and acknowledgement of possible charges.
Do not run old benchmark commands from historical integration guides.

Offline build-policy checks are listed in [the build guide](docker-build.md).
Those checks test source constraints, not AI accuracy or provider latency.
