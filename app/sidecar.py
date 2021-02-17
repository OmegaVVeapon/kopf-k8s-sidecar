import os
import asyncio
import threading
import contextlib
from misc import get_required_env_var, get_env_var_bool, get_env_var_int, log_env_vars
from io_helpers import write_file, delete_file
from conditions import label_is_satisfied, resource_is_desired
from list_mode import one_run
import kopf

@kopf.on.startup()
def startup_tasks(settings: kopf.OperatorSettings, logger, **_):
    """Perform all necessary startup tasks here. Keep them lightweight and relevant
    as the other handlers won't be initialized until these tasks are complete"""

    # Log some useful variables for troubleshooting
    log_env_vars(logger)

    # Replace the default marker with something less cryptic
    settings.persistence.finalizer = 'kopf.zalando.org/K8sSidecarFinalizerMarker'

    # Set the client and service k8s API timeouts
    # Very important! Without proper values, the operator may stop responding!
    # See https://github.com/nolar/kopf/issues/585
    client_timeout = get_env_var_int('WATCH_CLIENT_TIMEOUT', 660, logger)
    server_timeout = get_env_var_int('WATCH_SERVER_TIMEOUT', 600, logger)

    # Running the operator as a standalone
    # https://kopf.readthedocs.io/en/stable/peering/?highlight=standalone#standalone-mode
    settings.peering.standalone = True

    logger.info(f"Client watching requests using a timeout of {client_timeout} seconds")
    settings.watching.client_timeout = client_timeout

    logger.info(f"Server watching requests using a timeout of {server_timeout} seconds")
    settings.watching.server_timeout = server_timeout

    # The client timeout shouldn't be shorter than the server timeout
    # https://kopf.readthedocs.io/en/latest/configuration/#api-timeouts
    if client_timeout < server_timeout:
        logger.warning(f"The client timeout ({client_timeout}) is shorter than the server timeout ({server_timeout}). Consider increasing the client timeout to be higher")

    # Set k8s event logging
    settings.posting.enabled = get_env_var_bool('EVENT_LOGGING')

@kopf.on.resume('', 'v1', 'configmaps', when=kopf.all_([label_is_satisfied, resource_is_desired]))
@kopf.on.create('', 'v1', 'configmaps', when=kopf.all_([label_is_satisfied, resource_is_desired]))
@kopf.on.update('', 'v1', 'configmaps', when=kopf.all_([label_is_satisfied, resource_is_desired]))
@kopf.on.resume('', 'v1', 'secrets', when=kopf.all_([label_is_satisfied, resource_is_desired]))
@kopf.on.create('', 'v1', 'secrets', when=kopf.all_([label_is_satisfied, resource_is_desired]))
@kopf.on.update('', 'v1', 'secrets', when=kopf.all_([label_is_satisfied, resource_is_desired]))
def cru_fn(body, reason, logger, **_):
    write_file(reason, body, body['kind'], logger)

@kopf.on.delete('', 'v1', 'configmaps', when=kopf.all_([label_is_satisfied, resource_is_desired]))
@kopf.on.delete('', 'v1', 'secrets', when=kopf.all_([label_is_satisfied, resource_is_desired]))
def delete_fn(body, logger, **_):
    delete_file(body, body['kind'], logger)

def kopf_thread(
        ready_flag: threading.Event,
        stop_flag: threading.Event,
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with contextlib.closing(loop):

        # Since we're using an embedded operator we can't rely on CLI options to configure the logger
        # we have to do it here, before we start the operator
        kopf.configure(
            debug=get_env_var_bool("DEBUG"),
            verbose=get_env_var_bool("VERBOSE")
        )

        liveness_endpoint = None

        if os.getenv("LIVENESS") == 'false':
            print("Liveness /healthz endpoint has been explicitely disabled!")
        else:
            liveness_endpoint = "http://0.0.0.0:8080/healthz"
            print(f"Exposing liveness endpoint in {liveness_endpoint}")

        # Here we set the scoping for the operator
        # We will either check for Secrets and Configmaps in the entire cluster or a subset of namespaces
        namespace = os.getenv('NAMESPACE')

        clusterwide = None
        namespaces = []

        if namespace is None or namespace == 'ALL':
            clusterwide = True
            print("Monitoring for resources in the entire cluster")
        else:
            namespaces = namespace.replace(" ", "").split(',')
            print(f"Monitoring for resources in the {namespaces} namespace(s) only")

        loop.run_until_complete(kopf.operator(
            liveness_endpoint=liveness_endpoint,
            clusterwide=clusterwide,
            namespaces=namespaces,
            ready_flag=ready_flag,
            stop_flag=stop_flag,
        ))

def main():
    method = os.getenv('METHOD', 'WATCH')

    # The Grafana Helm chart guys pass an empty string for METHOD env var instead of just leaving it unset so os.getenv doesn't work correctly...
    if not method:
        method = 'WATCH'

    if method == 'WATCH':
        ready_flag = threading.Event()
        stop_flag = threading.Event()
        thread = threading.Thread(target=kopf_thread, kwargs=dict(
            stop_flag=stop_flag,
            ready_flag=ready_flag,
        ))
        thread.start()
        ready_flag.wait()
    elif method == 'LIST':
        one_run()
    else:
        print(f"METHOD {method} is not supported! Valid METHODs are 'WATCH' or 'LIST'")

if __name__ == '__main__':
    main()
