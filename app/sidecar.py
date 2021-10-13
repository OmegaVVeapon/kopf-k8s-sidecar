import logging
import asyncio
import threading
import contextlib
import sidecar_settings
from io_helpers import write_file, delete_file
from conditions import *
from list_mode import one_run
import kopf

@kopf.on.startup()
def startup_tasks(settings: kopf.OperatorSettings, logger, **_):
    """Perform all necessary startup tasks here. Keep them lightweight and relevant
    as the other handlers won't be initialized until these tasks are complete"""

    # Running the operator as a standalone
    # https://kopf.readthedocs.io/en/stable/peering/?highlight=standalone#standalone-mode
    settings.peering.standalone = True

    settings.watching.client_timeout = sidecar_settings.WATCH_CLIENT_TIMEOUT
    settings.watching.server_timeout = sidecar_settings.WATCH_SERVER_TIMEOUT

    # Disable k8s event logging
    settings.posting.enabled = False

# Event types when not 'DELETED' can be 'ADDED', 'MODIFIED' and None. The latter being when the resource already existed when the operator started
@kopf.on.event('', 'v1', 'configmaps', when=kopf.all_([label_is_satisfied, resource_is_desired, resource_is_cru]))
@kopf.on.event('', 'v1', 'secrets', when=kopf.all_([label_is_satisfied, resource_is_desired, resource_is_cru]))
def cru_fn(body, event, logger, **_):
    write_file(event['type'], body, body['kind'], logger)

@kopf.on.event('', 'v1', 'configmaps', when=kopf.all_([label_is_satisfied, resource_is_desired, resource_is_deleted]))
@kopf.on.event('', 'v1', 'secrets', when=kopf.all_([label_is_satisfied, resource_is_desired, resource_is_deleted]))
def delete_fn(body, logger, **_):
    delete_file(body, body['kind'], logger)

def kopf_thread(
        ready_flag: threading.Event,
        stop_flag: threading.Event,
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with contextlib.closing(loop):

        opts = {
            "liveness_endpoint": f"http://0.0.0.0:{sidecar_settings.HEALTHCHECK_PORT}/healthz",
            "clusterwide": False,
            "namespaces": [],
            "ready_flag": ready_flag,
            "stop_flag": stop_flag
        }

        if sidecar_settings.NAMESPACE == 'ALL':
            opts['clusterwide'] = True
        else:
            opts['namespaces'] = sidecar_settings.NAMESPACE

        loop.run_until_complete(kopf.operator(**opts))

def main():

    if sidecar_settings.METHOD == 'WATCH':
        ready_flag = threading.Event()
        stop_flag = threading.Event()
        thread = threading.Thread(target=kopf_thread, kwargs=dict(
            stop_flag=stop_flag,
            ready_flag=ready_flag
        ))
        thread.start()
        ready_flag.wait()
    elif sidecar_settings.METHOD == 'LIST':
        one_run()
    else:
        raise Exception(f"METHOD {sidecar_settings.METHOD} is not supported! Valid METHODs are 'WATCH' or 'LIST'")

if __name__ == '__main__':
    main()
