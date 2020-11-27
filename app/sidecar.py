import kopf
from misc import require_env_var, get_env_var_bool
from io_helpers import create_folder, write_file, delete_file

# Check that the required environment variables are present before we start
FOLDER = require_env_var('FOLDER')
LABEL = require_env_var('LABEL')

@kopf.on.startup()
def startup_tasks(settings: kopf.OperatorSettings, logger, **_):
    """Perform all necessary startup tasks here. Keep them lightweight and relevant
    as the other handlers won't be initialized until these tasks are complete"""
    # Replace the default marker with something less cryptic
    settings.persistence.finalizer = 'kopf.zalando.org/K8sSidecarFinalizerMarker'

    # Set k8s event logging
    settings.posting.enabled = get_env_var_bool('EVENT_LOGGING')

    # Create the folder from which we will write/delete files
    create_folder(FOLDER, logger)

    if get_env_var_bool('UNIQUE_FILENAMES'):
        logger.info("Unique filenames will be enforced.")

@kopf.on.resume('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.create('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.update('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
def write_configmap(body, event, logger, **_):
    write_file(event, body, logger)

@kopf.on.resume('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
@kopf.on.create('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
@kopf.on.update('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
def write_secret(body, event, logger, **_):
    write_file(event, body, logger)

@kopf.on.delete('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.delete('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
def delete_fn(body, logger, **_):
    delete_file(body, logger)
