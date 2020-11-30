#!/bin/bash
set -e

if [ "$1" = 'kopf-k8s-sidecar' ]; then

    command=("kopf" "run" "sidecar.py" "--standalone")

    [[ "$VERBOSE" = "true" ]] && command+=("--verbose")
    [[ "$DEBUG" = "true" ]] && command+=("--debug")
    [ -n "$NAMESPACE" ] && [ "$NAMESPACE" != "ALL" ] && echo "Only watching resources from the ${NAMESPACE} namespace" && command+=("--namespace=${NAMESPACE}")

    [[ "$LIVENESS" = "false" ]] && echo "Liveness /healthz endpoint has been explicitely disabled!" || command+=("--liveness=http://0.0.0.0:8080/healthz")

    exec "${command[@]}"
fi

exec "$@"
