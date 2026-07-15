#!/usr/bin/env bash
set -euo pipefail

VALIDATOR_VERSION="${VALIDATOR_VERSION:-latest}"
US_CORE_VERSION="${US_CORE_VERSION:-9.0.0}"
VALIDATOR_DIR="${VALIDATOR_DIR:-$HOME/.cache/fhir-validator}"
RESOURCE="${1:-fhir/examples/us-core-patient-synth-0002.json}"
mkdir -p "$VALIDATOR_DIR"

if [[ "$VALIDATOR_VERSION" == "latest" ]]; then
  validator_url="https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar"
else
  validator_url="https://github.com/hapifhir/org.hl7.fhir.core/releases/download/$VALIDATOR_VERSION/validator_cli.jar"
fi

if [[ ! -s "$VALIDATOR_DIR/validator_cli.jar" ]]; then
  curl -fL "$validator_url" -o "$VALIDATOR_DIR/validator_cli.jar"
fi

java -Xmx2g -jar "$VALIDATOR_DIR/validator_cli.jar" \
  "$RESOURCE" \
  -version 4.0.1 \
  -ig "hl7.fhir.us.core#$US_CORE_VERSION" \
  -profile http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient \
  -tx n/a
