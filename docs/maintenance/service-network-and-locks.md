# Dependency locks and DNS/egress checkpoint

Date: 2026-10-21. OpenSpec: **30/30, implemented and archived**. This is not
live-cutover approval. No original evaluation service, configuration, key or data
was changed. The final review and CI correction are recorded in the
[archived task ledger](../../openspec/changes/archive/2026-10-21-remove-chinese-service-dependencies/tasks.md).

## Final review and CI correction: pass

The final review covered all three capabilities (11 requirements, 14 scenarios).
It exposed a CI-only fixture-path regression, which the user explicitly approved
fixing. The actual workflow preparation now creates one synthetic configuration
at the path shared by pytest and logging, with exclusive no-overwrite creation.
Its new regression fails before the fix and passes afterward. The build-policy
suite now passes 15/15. Executing the actual YAML step in a network-disabled
public-source container passes 140 tests/one known skip; the complete Python
suite passes 226/five known skips. Runtime application sources and the recorded
build/fixture hashes are unchanged, so the passing network evidence below is
retained rather than claiming a new live rehearsal. Main specs were synchronized,
strict validation passed and the change was archived on 2026-10-21.

## Production dependency locking: pass

The reviewed Linux ARM64 production build now verifies 798 Maven input artifacts,
191 Debian archives and 27 APK archives before executing Maven or installers.
Base image digests cover packages already present in each base. Exact archive
sizes and SHA-256, HTTPS origins, declaration hashes and installed identities
are checked; missing, changed, additional or redirected artifacts fail closed.
Maven compilation and OS installation run with Docker networking disabled.

Python retains its existing exact wheel/hash lock. npm retains existing exact
versions/integrities and official-registry URLs. Installation scripts are now
disabled during web acquisition. Two reviewed local-file-only Vue initializers
(`vue-demi` and `v-code-diff`) run explicitly offline, followed by offline web
compilation. Omitting those initializers first exposed an expected missing-entry
build error; the final source build passes without enabling general hooks.

Clean artifact acquisition/builds succeeded. Main independently rechecked the
final exports: 120 bundled Java library hashes, 36 manager OS releases, 296
voice OS identities and 70 Python versions are preserved; zero operator Spring
profile entries exist in the JAR. Tests pass: 17 Python lock tests, Java positive
plus five negatives, five APK negatives, 14 build-policy and seven npm checks.
The complete identities/limits are in `service-dependency-lock-validation.json`.
No image was pushed or substituted into the evaluation deployment.

The lock targets the reviewed production Maven goal, not all possible test or
future plugin goals/platforms. Changed POMs/base digests require explicit review
and lock regeneration. Upstream archive removal causes failure, not an upgrade.
These component records are not vulnerability/license certification or a formal
supply-chain attestation. Test-only observer tooling is recorded separately.

## Full application scenario matrix: pass after approved local-IP fix

The test-only `tools/compose.service-egress.yaml` overlays only the explicitly
named, labelled synthetic candidate. A gate holds application startup until its
DNS witness and kernel OUTPUT rules are ready. A read-only portable strace bundle
starts before Java/nginx, Python and Node exec, following their ordinary threads
and descendants. A separate traced helper exercises removed-feature paths.

Observation covers connect/sendto/sendmsg/sendmmsg, IPv4/IPv6, failed attempts,
accepted TCP response direction, and child bookkeeping. Usable/submitted
`io_uring` fails closed; Node's three kernel-refused setup probes created no ring
and are recorded as non-I/O events. No privileged/unconfined or host-PID access
was used. Only the fixture container has namespace firewall administration.

The DNS fixture has no forwarding code and only answers the two candidate
service names plus localhost. Unknown question names are represented by hashes,
never echoed. Four real startup questions (A/AAAA for candidate-db/redis) were
observed. The exact-target firewall permits the local service ports and the
candidate DB/Redis endpoints, plus established replies. The UDP client exports
its exact ephemeral port instead of permitting a destination range.

Three negative controls exercise an unknown DNS name, a nonpermitted TCP port,
and DNS sent to a nonpermitted server. This repeat detected one unknown DNS
question and two numeric attempts, with two firewall drops and no parse errors.
The resolver and firewall counters were reset before starting the applications;
negative-control traffic is not included in application acceptance counters.
The initial rehearsal's handled EPERM fixture correction remains historical
evidence in the previous run, not a failure in this control repeat.

| Exercised path | Functional result |
| --- | --- |
| Accounts, CAPTCHA, permissions, binding, providers, history/audio, snapshots | 22/22 scenarios; 94 HTTP requests |
| Direct authenticated WS | 20 incoming Opus packets; six valid non-silent outputs |
| Signed MQTT + UDP/AES | Same valid audio framing/output, real MQTT control and device MCP replies |
| History permissions plus internal title/summary persistence | 2/2 scenarios; 15 HTTP requests |
| Removed endpoints/provider/tools/location | Eight endpoint rejections, one provider rejection, five stale tools unavailable, no location lookup |

Title/summary endpoints use the existing server-to-server secret, not ordinary
user credentials. An initial fixture call with an owner token correctly returned
401; the corrected fixture uses the known synthetic secret, then verifies saved
memory through the owner's API. Authentication was not disabled. A helper
initialization and a UDP-port-export argument bug were also fixed in test code;
their failed attempts are not presented as passing scenarios.

Final fake counters prove two ASR, two streamed chat, two TTS, three title and one
summary call, with zero invalid HTTP contracts. These are deterministic local
fakes, not evidence of real AI quality or permission to send child data elsewhere.
The parser passed all 75 Linux tests including actual strace; DNS and report
helpers passed seven and six offline tests respectively.

### Initial finding and approved correction

The initial combined network gate returned **failure**: Python made two UDP connect
attempts to **8.8.8.8:80**, both ENETUNREACH. `get_local_ip()` uses that address
to discover a local interface address. Its business AST matches baseline HEAD,
so this is pre-existing, not introduced by locking or translation. It is not a
DNS lookup or evidence of data exfiltration, but it violates the exact no-unknown
attempt contract even without a packet reaching the firewall. All four role
traces have zero parse errors. No allowlist exception was added for this target.

The user explicitly approved the narrow correction and isolated repeat.
`get_local_ip()` now reads active interface addresses/states through the already
locked `psutil` dependency. It returns the first usable IPv4 address in OS order,
or the existing loopback fallback. It performs no outbound connection or DNS
probe. Local interface reads may use OS ioctl/netlink; they do not select a
route by contacting an Internet host. On multihomed hosts the result is an
advertised-address hint, not a per-peer route decision.

Nine new regressions cover interface state, IPv4 selection, invalid/loopback
addresses, enumeration order and read failures, with socket/DNS APIs forbidden.
They reproduce the old network-probe violation and pass after the correction.
The complete offline Python suite passes **226 tests**, with the same five
documented skips. Its fixture needed writable scratch space for legacy tests;
all source copies/configuration remained synthetic and isolated.

The voice image was rebuilt without networking from the locked base. A fresh
candidate used that image and the final locked manager. An early voice start
before synthetic-key seeding correctly failed authentication (two permitted
HTTP connects, zero denied attempts/parse errors); its traced retry after
seeding passed. No authentication or endpoint policy was relaxed.

The final network gate **passes**: manager 137, voice 77, gateway seven and
removed-feature helper two Internet-family syscall observations, all permitted;
all four traces have zero denied attempts and zero parse errors. DNS recorded
only the four candidate DB/Redis questions, with zero rejected or forwarded
queries. IPv4 and IPv6 firewall unexpected-drop counters are both zero. All
functional scenarios above passed again with the recorded fake HTTP counts.
Tasks 7.1 and 7.5 are complete. Implementation acceptance does not authorize rollout.

## Provenance, cleanup and replay boundary

`service-network-validation.json` contains sanitized per-role/phase destination
counts, DNS questions, negative-control and firewall results, exact application
image IDs and limits. This passing run used the final dependency-locked images;
the initial failed report is preserved under `previousRun`, not overwritten as
a pass. `service-dependency-lock-validation.json` records the rebuilt voice
identity and unchanged 70 Python/296 OS components. The manager's 120 Java
libraries/36 OS identities and absence of operator profiles were rechecked too.
MySQL/Redis and fake AI are isolated fixture infrastructure, not traced
application roles. This is a bounded application witness, not adversarial
containment or a claim about unexercised providers/configurations.

For replay, use fresh synthetic fixtures from the approved parent candidate
README, both explicit Compose files, `--env-file`, project
`xiaozhi-policy-rehearsal`, and verified project/validation labels. Never use
the evaluation compose/configuration. Prepare the public strace+loader+libc
bundle and the two-service DNS mapping; initialize the audit volume; start the
gated manager; apply the namespace firewall; complete/reset the negative
controls; then open startup and record each named phase with
`service-network-report.py phase`. Run seed/API, WS, MQTT with exact port export,
summary and removed-feature fixtures; stop apps, record finish, and evaluate
`service-network-report.py report`. A nonzero result is a failed gate, not an
instruction to widen its policy. This is an operator-controlled rehearsal, not
an automatic launch against arbitrary container names.

All seven candidate containers, their internal network and six synthetic
volumes were removed after retaining sanitized evidence. Raw traces were never
exported and were deleted with the audit volume. Original container IDs, image
IDs and start times match the initial read-only snapshot; all five evaluation
services remain healthy. No commit, push, live cutover or paid provider call
occurred.
