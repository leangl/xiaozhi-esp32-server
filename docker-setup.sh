#!/bin/sh
# Deliberately non-mutating replacement for the retired automatic installer.
set -eu

printf '%s\n' \
  'Automatic installation/upgrades are unavailable in the supported profile.' \
  'No Docker daemon settings, containers, packages, models, or private files were changed.' \
  'Build reviewed local candidate images using docs/docker-build.md.' \
  'Rehearse with separate ports/volumes, verify backups, and obtain cutover approval.' \
  'See docs/Deployment.md or docs/Deployment_all.md for configuration requirements.'

case "${1:---help}" in
  --help|-h) exit 0 ;;
  *) printf '%s\n' 'No deployment action is supported by this script.' >&2; exit 2 ;;
esac
