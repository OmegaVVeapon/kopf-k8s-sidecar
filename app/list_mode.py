import logging
import pykube
from requests.exceptions import HTTPError
from urllib3.exceptions import ProtocolError
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
def write_configmaps(namespace, label):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        # This returns a Query object (https://codeberg.org/hjacobs/pykube-ng/src/branch/main/pykube/query.py)
        # Accessing its __len__ or __iter__ methods as done below will call the k8s API and thus, has the potential to fail
        configmaps = pykube.ConfigMap.objects(api).filter(
            namespace=namespace,
            selector=label
        )

        if not configmaps:
            logger.info("No configmaps found with label %s", label)
            return

        for configmap in configmaps:
            write_file("create", configmap.obj, configmap.kind, logger)
    except (HTTPError, ProtocolError) as api_error:
        logger.exception("The connection to the Kubernetes API server has failed!")
        raise api_error
    except Exception:
        logger.exception("Unexpected exception...")
        raise

@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(2),
    before_sleep=show_attempts_and_sleep_time
)
def write_secrets(namespace, label):
    try:
        api = pykube.HTTPClient(pykube.KubeConfig.from_env())
        # This returns a Query object (https://codeberg.org/hjacobs/pykube-ng/src/branch/main/pykube/query.py)
        # Accessing its __len__ or __iter__ methods as done below will call the k8s API and thus, has the potential to fail
        secrets = pykube.Secret.objects(api).filter(
            namespace=namespace,
            selector=label
        )
        if not secrets:
            logger.info("No secrets found with label %s", label)
            return

        for secret in secrets:
            write_file("create", secret.obj, secret.kind, logger)
    except (HTTPError, ProtocolError) as api_error:
        logger.exception("The connection to the Kubernetes API server has failed!")
        raise api_error
    except Exception:
        logger.exception("Unexpected exception...")
        raise

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

            write_configmaps(namespace, label)

    if sidecar_settings.RESOURCE in ('secret', 'both'):
        logger.info("Looking for secrets...")

        for namespace in namespaces:
            if namespace != pykube.all:
                logger.info("Searching in namespace %s", namespace)

            write_secrets(namespace, label)

    logger.info("LIST mode completed. Exiting...")
