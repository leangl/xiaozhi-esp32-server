# Source upgrades

The previous automatic-update recipes are unavailable in the supported profile.
They fetched source through a proxy, reset checkouts and killed/restarted running
processes. Use a separate candidate checkout and the
[source-build procedure](docker-build.md) instead. `docker-setup.sh` now prints
guidance without changing packages, Docker settings, private files or services.

Record the exact source revision and dirty-source input hashes. Resolve the
documented image, dependency-lock and model-provenance gates. Build all owned
backend artifacts from that candidate; preserve old artifacts for rollback.
Do not overwrite the live checkout or copy credentials into image build contexts.

Rehearse forward migrations on disposable data copies. Use separate Compose
project names, ports and volumes, local AI fixtures and externally enforced egress
capture. Verify account/device/history and transport contracts before promotion.
Liquibase applies new migrations; keep historical migration bytes unchanged.

Verify restorable backups and obtain cutover approval before restarting services.
Restore matched application/data backups for rollback and preserve newer writes
separately. Keep removed-provider egress blocked after rollback. The full backup
and verification checklist lives in [the build guide](docker-build.md#rehearsal-and-rollback).

Port 8001 remains the frontend development server. Production uses built static
assets with the management API on port 8002; disabling automatic upgrades does
not change that API or the device protocols.
