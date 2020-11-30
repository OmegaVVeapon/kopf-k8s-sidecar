import os
import sys

def get_required_env_var(name):
    """Returns value of a required environment variable. Fails if not found"""
    try:
        return os.environ[name]
    except KeyError:
        print(f"{name} environment variable is required! Exiting.")
        sys.exit(1)

def get_env_var_bool(name):
    """Gets value of environment variable as a boolean. If not 'true', returns False"""
    return os.getenv(name) == 'true'

def get_env_var_int(name, default, logger):
    """Gets value of environment variable as a boolean. If not a valid int,
    returns the given default value"""
    env_var = os.getenv(name, default)
    try:
        return int(env_var)
    except TypeError:
        logger.warning(f"""Expected an integer value for {name} and got {env_var}.
Using default {default} instead""")
