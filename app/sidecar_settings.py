#  import logging
from misc import *

logger = logging.getLogger(__name__)

# TODO: Set the log level from the env variable 
logging.basicConfig(format='[%(asctime)s] %(name)-30.30s %(funcName)-16.16s [%(levelname)-8.8s] %(message)s', level=logging.INFO)

LABEL = get_required_env_var('LABEL')
LABEL_VALUE = os.getenv('LABEL_VALUE')
if LABEL_VALUE:
    logger.info("Looking for resources with LABEL '%s' and LABEL_VALUE '%s'", LABEL, LABEL_VALUE)
else:
    logger.info("Looking for resources with LABEL '%s'", LABEL)

FOLDER = get_required_env_var('FOLDER')
logger.info("The default FOLDER to write files to is %s", FOLDER)

FOLDER_ANNOTATION = os.getenv('FOLDER_ANNOTATION', 'k8s-sidecar-target-directory')
logger.info("FOLDER_ANNOTATION for the destination folder is '%s'", FOLDER_ANNOTATION)

NAMESPACE = os.getenv('NAMESPACE', 'ALL')
if NAMESPACE == 'ALL':
    logger.info("Looking for resources in the entire cluster")
else:
    NAMESPACE = NAMESPACE.replace(" ", "").split(',')
    logger.info(f"Looking for resources ONLY in the {NAMESPACE} namespaces")

# Check that the user set a sane value for RESOURCE
RESOURCE = os.getenv('RESOURCE', 'configmap')
valid_resources = ['configmap', 'secret', 'both']
if RESOURCE not in valid_resources:
    raise Exception(f"RESOURCE should be one of [{', '.join(valid_resources)}]. Resources won't match until this is fixed!")
else:
    if RESOURCE == 'both':
        logger.info("Monitoring configmap and secret resources for changes")

METHOD = os.getenv('METHOD', 'WATCH')
# The Grafana Helm chart guys pass an empty string for METHOD env var instead of just leaving it unset so os.getenv doesn't work correctly...
if not METHOD:
    METHOD = 'WATCH'
logger.info("Using the %s METHOD", METHOD)

DEFAULT_FILE_MODE = os.getenv('DEFAULT_FILE_MODE')
if DEFAULT_FILE_MODE:
    #TODO: This conversion can fail depending on the given input. Add exception handling
    DEFAULT_FILE_MODE = int(DEFAULT_FILE_MODE, base=8)
logger.info("DEFAULT_FILE_MODE is %s", DEFAULT_FILE_MODE)

VERBOSE = get_env_var_bool("VERBOSE")
if VERBOSE:
    logger.info("VERBOSE mode is activated!")

DEBUG = get_env_var_bool("DEBUG")
if DEBUG:
    logger.info("DEBUG mode is activated!")

# Set the client and service k8s API timeouts
# Very important! Without proper values, the operator may stop responding!
# See https://github.com/nolar/kopf/issues/585
WATCH_CLIENT_TIMEOUT = get_env_var_int('WATCH_CLIENT_TIMEOUT', 660)
logger.info("Client watching requests using a timeout of %d seconds", WATCH_CLIENT_TIMEOUT)

WATCH_SERVER_TIMEOUT = get_env_var_int('WATCH_SERVER_TIMEOUT', 600)
logger.info("Server watching requests using a timeout of %d seconds", WATCH_SERVER_TIMEOUT)

# The client timeout shouldn't be shorter than the server timeout
# https://kopf.readthedocs.io/en/latest/configuration/#api-timeouts
if WATCH_CLIENT_TIMEOUT < WATCH_SERVER_TIMEOUT:
    logger.warning("The client timeout (%s) is shorter than the server timeout (%s). Consider increasing the client timeout to be higher", WATCH_CLIENT_TIMEOUT, WATCH_SERVER_TIMEOUT)

UNIQUE_FILENAMES = get_env_var_bool('UNIQUE_FILENAMES')
if get_env_var_bool('UNIQUE_FILENAMES'):
    logger.info("Unique filenames will be enforced.")
