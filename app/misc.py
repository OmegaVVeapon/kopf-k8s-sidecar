import os
import sys
import base64
import pykube

def get_required_env_var(name):
    """Returns value of a required environment variable. Fails if not found"""
    try:
        return os.environ[name]
    except KeyError as missing_env_var:
        raise Exception(f"{name} environment variable is required! Exiting.") from missing_env_var

def get_env_var_bool(name):
    """Gets value of environment variable as a boolean. If not 'true', returns False"""
    return os.getenv(name) == 'true'

def get_env_var_int(name, default, logger):
    """Gets value of environment variable as an int. If not a valid int,
    returns the given default value"""
    env_var = os.getenv(name, default)
    try:
        return int(env_var)
    except TypeError:
        logger.warning(f"""Expected an integer value for {name} and got {env_var}.
Using default {default} instead""")

def get_base64_decoded(content):
    """Returns the base64-decoded content"""
    return base64.b64decode(content).decode()

def get_method():
    method = os.getenv('METHOD', 'WATCH')

    # The Grafana Helm chart guys pass an empty string for METHOD env var instead of just leaving it unset so os.getenv doesn't work correctly...
    if not method:
        method = 'WATCH'

    return method

def get_scope():
    """Returns a dictionary with the scoping necessary for either the WATCH
    mode or the LIST mode"""

    method = get_method()
    namespace = os.getenv('NAMESPACE')

    ret = {
        'clusterwide': False,
        'namespaces': []
    }

    if namespace is None or namespace == 'ALL':
        ret['clusterwide'] = True
        if method == 'LIST':
            ret['namespaces'] = [pykube.all]
    else:
        ret['namespaces'] = namespace.replace(" ", "").split(',')

    return ret


def log_env_vars(logger):
    """Logs the env vars set by the user by for easy troubleshooting.
    Meant to be called at the start of the operator or the list mode codepath"""

    method = get_method()
    logger.info(f"Using the {method} METHOD")

    folder = get_required_env_var('FOLDER')
    logger.info(f"The default FOLDER to write files to is {folder}")

    folder_annotation = os.getenv('FOLDER_ANNOTATION')
    if not folder_annotation:
        logger.info("FOLDER_ANNOTATION not set. Defaulting to look for 'k8s-sidecar-target-directory'")
    else:
        logger.info(f"FOLDER_ANNOTATION that we will look for to override the destination folder is '{folder_annotation}'")

    label = get_required_env_var('LABEL')
    label_value = os.getenv('LABEL_VALUE')
    if label_value:
        logger.info(f"Looking for resources with LABEL '{label}' and LABEL_VALUE '{label_value}'")
    else:
        logger.info(f"Looking for resources with LABEL '{label}'")

    # Check that the user set a sane value for RESOURCE
    resource = os.getenv('RESOURCE', 'configmap')
    valid_resources = ['configmap', 'secret', 'both']
    if resource not in valid_resources:
        logger.error(f"RESOURCE should be one of [{', '.join(valid_resources)}]. Resources won't match until this is fixed!")
    else:
        if resource == 'both':
            resource = 'configmap and secret'
        logger.info(f"Monitoring {resource} resources for changes")

    if get_env_var_bool('UNIQUE_FILENAMES'):
        logger.info("Unique filenames will be enforced.")

    scope = get_scope()
    if scope['clusterwide']:
        logger.info("Looking for resources in the entire cluster")
    else:
        logger.info(f"Looking for resources ONLY in the {scope['namespaces']} namespaces")
