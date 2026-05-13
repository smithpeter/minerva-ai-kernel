#!/usr/bin/env bash
# Intentionally-failing build for Minerva sample-consumer.
#
# The point of this script is to exit non-zero with a typical Python
# import error, so that the Minerva diagnose workflow has something
# realistic to chew on. Do NOT install pyyaml — the failure is the
# product.

set -uo pipefail

python3 app/sample_app.py
exit_code=$?

echo "build exited with code ${exit_code}"
exit "${exit_code}"
