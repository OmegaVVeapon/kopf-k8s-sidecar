import os
import sys

def require_env_var(name):
    """Returns value of a required environment variable. Fails if not found"""
    try:
        return os.environ[name]
    except KeyError:
        print(f"{name} environment variable is required! Exiting.")
        sys.exit(1)

def get_env_var_bool(name):
    """Gets value of environment variable as a boolean. If not 'true', returns False"""
    return os.getenv(name) == 'true'
