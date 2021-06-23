import os
import logging

logger = logging.getLogger(__name__)

def get_required_env_var(name):
    """Returns value of a required environment variable. Fails if not found"""
    try:
        return os.environ[name]
    except KeyError as missing_env_var:
        raise Exception(f"{name} environment variable is required! Exiting.") from missing_env_var

def get_env_var_bool(name):
    """Gets value of environment variable as a boolean. If not 'true', returns False"""
    return os.getenv(name) == 'true'

def get_env_var_int(name, default):
    """Gets value of environment variable as an int. If not a valid int,
    returns the given default value"""
    env_var = os.getenv(name, default)
    try:
        return int(env_var)
    except TypeError:
        logger.warning("""Expected an integer value for %s and got %s.
Using default %s instead""", name, env_var, default)
