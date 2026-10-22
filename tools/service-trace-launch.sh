#!/bin/sh
# Candidate-only gate, followed by payload-free tracing from first app exec.
set -eu
test "${CANDIDATE_EGRESS_FIXTURE:-}" = service-policy-rehearsal-20261021
role=${1:?candidate role required}
case "$role" in
  manager) set -- /bin/bash /start.sh ;;
  voice) set -- python app.py ;;
  gateway) set -- node app.js ;;
  *) exit 64 ;;
esac
umask 022
# The DNS witness and namespace allowlist must be ready before any app starts.
while test ! -f /audit-out/start-apps; do sleep 1; done
exec /audit/ld-linux-aarch64.so.1 --library-path /audit /audit/strace \
  -f -qq -ttt -s 0 -v -yy -e signal=none \
  -e trace=connect,sendto,sendmsg,sendmmsg,io_uring_setup,io_uring_enter,io_uring_register,clone,clone3,fork,vfork \
  -o "/audit-out/$role.trace" -- "$@"
