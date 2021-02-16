import os
import pykube
from io_helpers import write_file
from conditions import label_is_satisfied
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

    # Get the user-defined namespace, if not specified (or if "ALL"), look in all of them
    namespace = os.getenv("NAMESPACE", pykube.all)
    if namespace == "ALL":
        namespace = pykube.all

    resource = os.getenv('RESOURCE', 'configmap')

    if resource in ('configmap', 'both'):
        configmaps = _get_configmaps(namespace)
        for configmap in configmaps:
            if label_is_satisfied(configmap.obj['metadata']):
                write_file("create", configmap.obj, configmap.kind, logger)

    if resource in ('secret', 'both'):
        secrets = _get_secrets(namespace)
        for secret in secrets:
            if label_is_satisfied(secret.obj['metadata']):
                write_file("create", secret.obj, secret.kind, logger)
