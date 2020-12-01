import os
import errno
import hashlib
from misc import get_env_var_bool

def create_folder(folder, logger):
    """
    If the parent folder doesn't exist, create it. If there are insufficient
    permissions to create the directory, log an error and return.
    """
    if not os.path.exists(folder):
        logger.info(f"Creating folder {folder}")
        try:
            os.makedirs(folder)
        except OSError as e:
            if e.errno not in (errno.EACCES, errno.EEXIST):
                raise
            if e.errno == errno.EACCES:
                logger.error(f"Insufficient privileges to create folder {folder}.")
                return
    logger.info(f"Folder {folder} already exists. Skipping creation.")

async def get_filepath(filename, body):
    """
    Returns unique path if UNIQUE_FILENAMES are desired.
    Otherwise, simply returns the concatenated filename with the folder.
    """
    folder = os.environ['FOLDER']

    if get_env_var_bool('UNIQUE_FILENAMES'):
        namespace = 'default'
        if 'namespace' in body['metadata']:
            namespace = body['metadata']['namespace']

        name = body['metadata']['name']
        kind = body['kind'].lower()

        filename = namespace + "." + kind + "_" + name + "." + filename

    return os.path.join(folder, filename)


async def delete_file(body, logger):
    resource_kind = body['kind']

    for filename in body['data'].keys():
        filepath = await get_filepath(filename, body)
        logger.info(f"[DELETE:{resource_kind}] Deleting file {filepath}.")
        try:
            os.remove(filepath)
        except FileNotFoundError:
            logger.error(f"[DELETE:{resource_kind}] {filepath} not found.")
        except OSError as e:
            logger.error(e)

async def write_file(event, body, logger):
    """
    Write contents to the desired filepath if they have changed.
    """
    resource_kind = body['kind']
    event = event.upper()

    for filename, content in body['data'].items():
        filepath = await get_filepath(filename, body)

        if os.path.exists(filepath):
            # Compare file contents with new ones so we don't update the file if nothing changed
            sha256_hash_new = hashlib.sha256(content.encode('utf-8'))
            with open(filepath, 'rb') as f:
                sha256_hash_cur = hashlib.sha256()
                for byte_block in iter(lambda: f.read(4096),b""):
                    sha256_hash_cur.update(byte_block)

            if sha256_hash_new.hexdigest() == sha256_hash_cur.hexdigest():
                logger.info(f"[{event}:{resource_kind}] Contents of {filepath} haven't changed. Not overwriting existing file.")
                continue

        try:
            with open(filepath, 'w') as f:
                logger.info(f"[{event}:{resource_kind}] Writing content to file {filepath}")
                f.write(content)
        # TODO: Flesh out IO exception handling here
        except Exception as e:
            logger.error(e)

        if os.getenv('DEFAULT_FILE_MODE'):
            mode = int(os.getenv('DEFAULT_FILE_MODE'), base=8)
            os.chmod(filepath, mode)
