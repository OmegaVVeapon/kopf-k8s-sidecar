#!/bin/bash
set -e

if [ "$1" = 'kopf-k8s-sidecar' ]; then

    # command=("kopf" "run" "sidecar.py")
    command=("python" "sidecar.py")

    # [[ "$VERBOSE" = "true" ]] && command+=("--verbose")
    # [[ "$DEBUG" = "true" ]] && command+=("--debug")
    # [ -n "$NAMESPACE" ] && [ "$NAMESPACE" != "ALL" ] && echo "Only watching resources from the ${NAMESPACE} namespace" && command+=("--namespace=${NAMESPACE}")

    # [[ "$LIVENESS" = "false" ]] && echo "Liveness /healthz endpoint has been explicitely disabled!" || command+=("--liveness=http://0.0.0.0:8080/healthz")

    # Fix https://github.com/OmegaVVeapon/kopf-k8s-sidecar/issues/12 by setting the USER env var to prevent python from looking for a matching uid/gid in the password database.
    # See https://github.com/python/cpython/blob/v3.6.0/Lib/getpass.py#L155-L170.
    USER=$(id --user)
    echo "Setting USER environment variable to ${USER}"
    export USER=$USER

    exec "${command[@]}"
fi

exec "$@"
