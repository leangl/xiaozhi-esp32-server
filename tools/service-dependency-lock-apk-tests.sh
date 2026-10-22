#!/bin/sh
# Synthetic pre-install failures: the apk stub must never reach add.
set -eu
tool=${1:-/opt/service-dependency-lock-apk.sh}
work=$(mktemp -d)
trap 'rm -rf "$work" /tmp/locked-apk.*' EXIT
mkdir "$work/bin" "$work/archives"
printf reviewed > "$work/archives/fixture-1-r0.apk"
base=docker.io/bellsoft/liberica-runtime-container@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
{
    printf 'service-dependency-lock-v1\nkind\tapk\nbase\t%s\narch\taarch64\n' "$base"
    printf 'artifact\t%s\t8\tfixture-1-r0.apk\thttps://packages.bell-sw.com/fixture-1-r0.apk\tfixture:1-r0:aarch64\n' "$(sha256sum "$work/archives/fixture-1-r0.apk" | cut -d ' ' -f 1)"
} > "$work/fixture.lock"
cat > "$work/bin/apk" <<'STUB'
#!/bin/sh
if test "$1" = --print-arch; then echo aarch64; exit 0; fi
touch "$APK_EXECUTION_MARKER"
exit 77
STUB
chmod +x "$work/bin/apk"
export PATH="$work/bin:$PATH" APK_EXECUTION_MARKER="$work/executed"
reject() {
    if sh "$tool" "$work/fixture.lock" "$work/archives" "$base" > "$work/rejection.log" 2>&1; then
        echo 'FAIL: invalid APK input accepted'; exit 1
    fi
    test ! -e "$APK_EXECUTION_MARKER"
}
printf tampered > "$work/archives/fixture-1-r0.apk"
reject
printf reviewed > "$work/archives/fixture-1-r0.apk"
mv "$work/archives/fixture-1-r0.apk" "$work/artifact"
reject
mv "$work/artifact" "$work/archives/fixture-1-r0.apk"
printf unreviewed > "$work/archives/extra-1-r0.apk"
reject
rm "$work/archives/extra-1-r0.apk"
mkdir "$work/archives/unreviewed"
reject
rmdir "$work/archives/unreviewed"
mv "$work/archives/fixture-1-r0.apk" "$work/artifact"
ln -s "$work/artifact" "$work/archives/fixture-1-r0.apk"
reject
echo 'APK lock tests: tamper/missing/unreviewed/directory/symlink rejected before apk'
