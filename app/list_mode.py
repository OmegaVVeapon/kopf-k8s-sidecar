import logging
import pykube
from io_helpers import write_file
from tenacity import retry, stop_after_attempt, wait_fixed
import sidecar_settings

logger = logging.getLogger(__name__)

def show_attempts_and_sleep_time(retry_state):
    logger.info('Retrying %s: attempt %s ended with: %s',
        retry_state.fn, retry_state.attempt_number, retry_state.outcome)
    logger.info("Waiting 2 seconds to retry...")

@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(2),
    before_sleep=show_attempts_and_sleep_time
)
def _get_configmaps(namespace, label):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        configmaps = pykube.ConfigMap.objects(api).filter(
            namespace=namespace,
            selector=label
        )
    except pykube.exceptions.HTTPError as pykube_http_error:
        logger.exception("The connection to the Kubernetes API server has failed!")
        raise pykube_http_error
    except Exception:
        logger.exception("Unexpected non-HTTP exception...")
        raise
    else:
        return configmaps

@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(2),
    before_sleep=show_attempts_and_sleep_time
)
def _get_secrets(namespace, label):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        secrets = pykube.Secret.objects(api).filter(
            namespace=namespace,
            selector=label
        )
    except pykube.exceptions.HTTPError as pykube_http_error:
        logger.exception("The connection to the Kubernetes API server has failed!")
        raise pykube_http_error
    except Exception:
        logger.exception("Unexpected non-HTTP exception...")
        raise
    else:
        return secrets

def one_run():
    """Search through all the ConfigMaps and Secrets in the specified namespaces. If they meet the label requirements,
    copy the files to the destination. Update and delete operations not needed in this mode"""

    if sidecar_settings.NAMESPACE == 'ALL':
        namespaces = [pykube.all]
    else:
        namespaces = sidecar_settings.NAMESPACE

    if sidecar_settings.LABEL_VALUE:
        label = {sidecar_settings.LABEL: sidecar_settings.LABEL_VALUE}
    else:
        label = sidecar_settings.LABEL

    if sidecar_settings.RESOURCE in ('configmap', 'both'):
        logger.info("Looking for configmaps...")

        for namespace in namespaces:
            if namespace != pykube.all:
                logger.info("Searching in namespace %s", namespace)

            configmaps = _get_configmaps(namespace, label)

            if not configmaps:
                logger.info("No configmaps found with label %s", label)

            for configmap in configmaps:
                write_file("create", configmap.obj, configmap.kind, logger)

    if sidecar_settings.RESOURCE in ('secret', 'both'):
        logger.info("Looking for secrets...")

        for namespace in namespaces:
            if namespace != pykube.all:
                logger.info("Searching in namespace %s", namespace)

            secrets = _get_secrets(namespace, label)

            if not secrets:
                logger.info("No secrets found with label %s", label)

            for secret in secrets:
                write_file("create", secret.obj, secret.kind, logger)

    if not configmaps and not secrets:
        logger.warning("Could not find configmaps OR secrets matching label %s. Was this intended?", label)

    logger.info("LIST mode completed. Exiting...")
