import os
import logging
from io_helpers import write_file
import sidecar_settings

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

config.load_incluster_config()

v1 = client.CoreV1Api()

def _get_configmaps(kwargs):

    try:
        return v1.list_config_map_for_all_namespaces(**kwargs)
    except ApiException:
        logger.exception("Exception when calling CoreV1Api->list_config_map_for_all_namespaces")

def _get_secrets(kwargs):
    try:
        return v1.list_secret_for_all_namespaces(**kwargs)
    except ApiException:
        logger.exception("Exception when calling CoreV1Api->list_secret_for_all_namespaces")

def one_run():
    """Search through all the ConfigMaps and Secrets in the specified namespaces. If they meet the label requirements,
    copy the files to the destination. Update and delete operations not needed in this mode"""

    # This is a one-off operation, we don't need a stream...
    kwargs = dict(watch = False)

    if sidecar_settings.LABEL_VALUE:
        kwargs['label_selector'] = f"{sidecar_settings.LABEL}={sidecar_settings.LABEL_VALUE}"
    else:
        kwargs['label_selector'] = f"{sidecar_settings.LABEL}"

    if sidecar_settings.NAMESPACE == 'ALL':

        if sidecar_settings.RESOURCE in ('configmap', 'both'):
            configmaps = _get_configmaps(kwargs)

            if not configmaps.items:
                logger.warning("Could not find any configmaps with label %s", kwargs['label_selector'])

            for configmap in configmaps.items:
                write_file("create", configmap, "ConfigMap", logger)

        #  if sidecar_settings.RESOURCE in ('secret', 'both'):
        #      secrets = _get_secrets(kwargs)
    #  else:
    #      for namespace in sidecar_settings.NAMESPACE:

    #          kwargs['field_selector'] = f"metadata.namespace={namespace}"

    #          if sidecar_settings.RESOURCE in ('configmap', 'both'):
    #              configmaps = _get_configmaps(kwargs)
    #              for configmap in configmaps:
    #                  write_file("create", configmap.obj, configmap.kind, logger)

    #  if resource in ('configmap', 'both'):
    #      for namespace in scope['namespaces']:
    #          configmaps = _get_configmaps(namespace)
    #          for configmap in configmaps:
    #              if label_is_satisfied(configmap.obj['metadata']):
    #                  write_file("create", configmap.obj, configmap.kind, logger)

    #  if resource in ('secret', 'both'):
    #      for namespace in scope['namespaces']:
    #          secrets = _get_secrets(namespace)
    #          for secret in secrets:
    #              if label_is_satisfied(secret.obj['metadata']):
    #                  write_file("create", secret.obj, secret.kind, logger)
