#!/bin/bash
set -e

if [ "$1" = 'kopf-k8s-sidecar' ]; then

    command=("kopf" "run" "sidecar.py" "--standalone")

    [[ "$VERBOSE" = "true" ]] && command+=("--verbose")
    [[ "$DEBUG" = "true" ]] && command+=("--debug")
    [ -n "$NAMESPACE" ] && [ "$NAMESPACE" != "ALL" ] && command+=("--namespace=${NAMESPACE}")

    exec "${command[@]}"
fi

exec "$@"
