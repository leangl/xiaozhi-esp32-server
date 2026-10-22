#!/bin/sh
# Offline APK install; compatible with the pinned Alpaquita apk-tools 3 image.
set -eu
lock=$1
directory=$2
base=$3
test "$(head -n 1 "$lock")" = service-dependency-lock-v1
test "$(awk -F '\t' '$1 == "kind" { print $2 }' "$lock")" = apk
test "$(awk -F '\t' '$1 == "base" { print $2 }' "$lock")" = "$base"
test "$(awk -F '\t' '$1 == "arch" { print $2 }' "$lock")" = "$(apk --print-arch)"
# Locked archive basenames are deliberately restricted before passing to a shell.
awk -F '\t' '$1 == "artifact" { if (NF != 6 || $4 !~ /^[A-Za-z0-9_.+~-]+\.apk$/ || length($2) != 64 || $2 ~ /[^0-9a-f]/) exit 1; print $2 "  " $4 }' "$lock" > /tmp/locked-apk.sha256
test -s /tmp/locked-apk.sha256
awk -F '\t' '$1 == "artifact" { print $4 }' "$lock" | sort > /tmp/locked-apk.expected
(cd "$directory" && find . -mindepth 1 | sed 's|^./||' | sort) > /tmp/locked-apk.actual
test -z "$(find "$directory" -type l)"
cmp /tmp/locked-apk.expected /tmp/locked-apk.actual
(cd "$directory" && sha256sum -c /tmp/locked-apk.sha256)
# Absolute local archives only. Repository lookup and package scripts are disabled.
apk --no-network --repositories-file /dev/null add --no-scripts "$directory"/*.apk
awk -F '\t' '$1 == "installed" { print $2 }' "$lock" | sort > /tmp/locked-apk.installed.expected
apk --no-network info -v | sort > /tmp/locked-apk.installed.actual
cmp /tmp/locked-apk.installed.expected /tmp/locked-apk.installed.actual
rm /tmp/locked-apk.*
