import os
import pykube
from io_helpers import write_file
from conditions import label_is_satisfied
from misc import log_env_vars, get_scope
import logging

def _get_configmaps(namespace):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        configmaps = pykube.ConfigMap.objects(api).filter(namespace=namespace)
        return configmaps
    except pykube.exceptions.HTTPError as e:
        if e.code in [409]:
            pass
        else:
            raise

def _get_secrets(namespace):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        configmaps = pykube.Secret.objects(api).filter(namespace=namespace)
        return configmaps
    except pykube.exceptions.HTTPError as e:
        if e.code in [409]:
            pass
        else:
            raise

def one_run():
    """Search through all the ConfigMaps and Secrets in the specified namespaces. If they meet the label requirements,
    copy the files to the destination. Update and delete operations not needed in this mode"""

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Log some useful variables for troubleshooting
    log_env_vars(logger)

    scope = get_scope()

    resource = os.getenv('RESOURCE', 'configmap')

    if resource in ('configmap', 'both'):
        for namespace in scope['namespaces']:
            configmaps = _get_configmaps(namespace)
            for configmap in configmaps:
                if label_is_satisfied(configmap.obj['metadata']):
                    write_file("create", configmap.obj, configmap.kind, logger)

    if resource in ('secret', 'both'):
        for namespace in scope['namespaces']:
            secrets = _get_secrets(namespace)
            for secret in secrets:
                if label_is_satisfied(secret.obj['metadata']):
                    write_file("create", secret.obj, secret.kind, logger)
