#!/bin/sh
# Run only in a disposable JDK 21 Linux aarch64 test container, no network.
set -eu
tool=${1:-/opt/service-dependency-lock.java}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/repo/g/a/1" "$work/source/.mvn"
printf reviewed > "$work/repo/g/a/1/a-1.jar"
for input in pom.xml .mvn/settings.xml .mvn/maven.config; do printf public > "$work/source/$input"; done
base=docker.io/library/maven@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
{
    printf 'service-dependency-lock-v1\nkind\tmaven\nbase\t%s\narch\tlinux/aarch64\n' "$base"
    for input in pom.xml .mvn/settings.xml .mvn/maven.config; do
        printf 'input\t%s\t%s\n' "$(sha256sum "$work/source/$input" | cut -d ' ' -f 1)" "$input"
    done
    printf 'artifact\t%s\t8\tg/a/1/a-1.jar\thttps://repo.maven.apache.org/maven2/g/a/1/a-1.jar\tg:a:1:jar\n' "$(sha256sum "$work/repo/g/a/1/a-1.jar" | cut -d ' ' -f 1)"
} > "$work/fixture.lock"
verify() { java "$tool" verify "$work/fixture.lock" "$work/repo" "$base" "$work/source"; }
reject() { if verify > "$work/rejection.log" 2>&1; then echo 'FAIL: invalid fixture accepted'; exit 1; fi; }
verify
printf tampered > "$work/repo/g/a/1/a-1.jar"
reject
printf reviewed > "$work/repo/g/a/1/a-1.jar"
mv "$work/repo/g/a/1/a-1.jar" "$work/artifact"
reject
mv "$work/artifact" "$work/repo/g/a/1/a-1.jar"
printf unknown > "$work/repo/unreviewed.jar"
reject
rm "$work/repo/unreviewed.jar"
printf changed > "$work/source/pom.xml"
reject
printf public > "$work/source/pom.xml"
base=docker.io/library/maven@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
reject
echo 'Java lock tests: positive + tamper/missing/unreviewed/POM/base negatives passed'
