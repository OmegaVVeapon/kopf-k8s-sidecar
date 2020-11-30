import os
import asyncio
import kopf
from misc import get_required_env_var, get_env_var_bool, get_env_var_int
from io_helpers import create_folder, write_file, delete_file

LABEL = None

@kopf.on.startup()
def startup_tasks(settings: kopf.OperatorSettings, logger, **_):
    """Perform all necessary startup tasks here. Keep them lightweight and relevant
    as the other handlers won't be initialized until these tasks are complete"""

    # Check that the required environment variables are present before we start
    folder = get_required_env_var('FOLDER', logger)
    LABEL = get_required_env_var('LABEL', logger)

    # Replace the default marker with something less cryptic
    settings.persistence.finalizer = 'kopf.zalando.org/K8sSidecarFinalizerMarker'

    # Set the client and service k8s API timeouts
    # Very important! Without proper values, the operator may stop responding!
    # See https://github.com/nolar/kopf/issues/585
    client_timeout = get_env_var_int('WATCH_CLIENT_TIMEOUT', 60, logger)
    server_timeout = get_env_var_int('WATCH_SERVER_TIMEOUT', 60, logger)

    # The client timeout shouldn't be shorter than the server timeout
    # https://kopf.readthedocs.io/en/latest/configuration/#api-timeouts
    if client_timeout < server_timeout:
        logger.warning(f"The client timeout ({client_timeout}) is shorter than the server timeout ({server_timeout}). Consider increasing the client timeout to be higher")

    # Set k8s event logging
    settings.posting.enabled = get_env_var_bool('EVENT_LOGGING')

    # Create the folder from which we will write/delete files
    create_folder(folder, logger)

    if get_env_var_bool('UNIQUE_FILENAMES'):
        logger.info("Unique filenames will be enforced.")

@kopf.on.resume('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.create('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.update('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.resume('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
@kopf.on.create('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
@kopf.on.update('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
async def cru_fn(body, event, logger, **_):
    try:
        await write_file(event, body, logger)
    except asyncio.CancelledError:
        logger.info(f"Write file cancelled for {body['kind']}")

@kopf.on.delete('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.delete('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
async def delete_fn(body, logger, **_):
    try:
        await delete_file(body, logger)
    except asyncio.CancelledError:
        logger.info(f"Delete file cancelled for {body['kind']}")
