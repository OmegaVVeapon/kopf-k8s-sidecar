import os
import kopf
from helpers import *

# Check that the required environment variables are present before we start
FOLDER = require_envvar('FOLDER')
LABEL = require_envvar('LABEL')

@kopf.on.startup()
def startup_tasks(settings: kopf.OperatorSettings, logger, **_):
    settings.persistence.finalizer = 'kopf.zalando.org/K8sSidecarFinalizerMarker'

    # Turn off k8s event logging unless EVENT_LOGGING exists
    if not "EVENT_LOGGING" in os.environ:
        settings.posting.enabled = False

    # Create the folder to which we will write our files
    create_folder(FOLDER, logger)

@kopf.on.resume('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.create('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.update('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
def write_configmap(body, event, logger, **_):
    write_file(event, FOLDER, body, logger)

@kopf.on.resume('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
@kopf.on.create('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
@kopf.on.update('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
def write_secret(body, event, logger, **_):
    write_file(event, FOLDER, body, logger)

@kopf.on.delete('', 'v1', 'configmaps', labels={LABEL: kopf.PRESENT})
@kopf.on.delete('', 'v1', 'secrets', labels={LABEL: kopf.PRESENT})
def delete_fn(body, logger, **_):
    delete_file(body, FOLDER, logger)
