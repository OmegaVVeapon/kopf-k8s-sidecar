import sys
import logging
import functools
import pykube
from io_helpers import write_file
from conditions import label_is_satisfied
from time import sleep
import sidecar_settings

logger = logging.getLogger(__name__)

def retry(retry_count=5, delay=5, allowed_exceptions=()):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            for _ in range(retry_count):
                try:
                    result = f(*args, **kwargs)
                    if result:
                        return result
                except allowed_exceptions as e:
                    pass
                logger.info("Waiting for %s seconds before trying again", delay)
                sleep(delay)
            logger.error("Failed the maximum of %d times... Exiting with error", retry_count)
            sys.exit(1)
        return wrapper
    return decorator

@retry(retry_count=5, delay=5)
def _get_configmaps(namespace):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        configmaps = pykube.ConfigMap.objects(api).filter(namespace=namespace)
        return configmaps
    except pykube.exceptions.HTTPError as e:
        logger.exception("The connection to the Kubernetes API server has failed!")

@retry(retry_count=5, delay=2)
def _get_secrets(namespace):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        configmaps = pykube.Secret.objects(api).filter(namespace=namespace)
        return configmaps
    except pykube.exceptions.HTTPError as e:
        logger.exception("The connection to the Kubernetes API server has failed!")

def one_run():
    """Search through all the ConfigMaps and Secrets in the specified namespaces. If they meet the label requirements,
    copy the files to the destination. Update and delete operations not needed in this mode"""

    if sidecar_settings.NAMESPACE == 'ALL':
        namespaces = [pykube.all]
    else:
        namespaces = sidecar_settings.NAMESPACE

    if sidecar_settings.RESOURCE in ('configmap', 'both'):
        logger.info("Looking for configmap resources with label %s and value %s", sidecar_settings.LABEL, sidecar_settings.LABEL_VALUE)

        for namespace in namespaces:
            configmaps = _get_configmaps(namespace)
            for configmap in configmaps:
                if label_is_satisfied(configmap.obj['metadata']):
                    write_file("create", configmap.obj, configmap.kind, logger)

    if sidecar_settings.RESOURCE in ('secret', 'both'):
        for namespace in namespaces:
            secrets = _get_secrets(namespace)
            for secret in secrets:
                if label_is_satisfied(secret.obj['metadata']):
                    write_file("create", secret.obj, secret.kind, logger)
