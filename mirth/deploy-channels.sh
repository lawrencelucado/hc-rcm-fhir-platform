#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${MIRTH_API_URL:-https://127.0.0.1:8443/api}"
ADMIN_USER="${MIRTH_ADMIN_USER:-admin}"
PASSWORD_FILE="${MIRTH_PASSWORD_FILE:-/opt/mirth-lab/.admin-password}"
CHANNEL_DIR="${CHANNEL_DIR:-/opt/mirth-lab/channels}"
cookie=$(mktemp)
trap 'rm -f "$cookie"' EXIT

password=$(<"$PASSWORD_FILE")
curl -ksSf -H 'X-Requested-With: OpenAPI' -c "$cookie" \
  -X POST --data-urlencode "username=$ADMIN_USER" --data-urlencode "password=$password" \
  "$BASE_URL/users/_login" >/dev/null

for channel in adt-to-fhir.xml dft-to-fhir.xml; do
  case "$channel" in
    adt-to-fhir.xml) channel_id=de82d30f-9f6e-4c03-ae21-0788cbdc6661 ;;
    dft-to-fhir.xml) channel_id=5ac2b9aa-b231-4bb3-8f43-e5959e1d6662 ;;
  esac
  curl -ksSf -H 'X-Requested-With: OpenAPI' -H 'Content-Type: application/xml' \
    -H 'Accept: text/plain' -b "$cookie" -X PUT --data-binary "@$CHANNEL_DIR/$channel" \
    "$BASE_URL/channels/$channel_id?override=true" >/dev/null
done

for channel_id in \
  de82d30f-9f6e-4c03-ae21-0788cbdc6661 \
  5ac2b9aa-b231-4bb3-8f43-e5959e1d6662; do
  curl -ksSf -H 'X-Requested-With: OpenAPI' -b "$cookie" -X POST \
    "$BASE_URL/channels/$channel_id/_deploy?returnErrors=true" >/dev/null
done

echo channels-deployed
