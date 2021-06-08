import os
import errno
import hashlib
import sidecar_settings
from misc import get_env_var_bool, get_base64_decoded

def create_folder(folder, logger):
    """
    If the parent folder doesn't exist, create it. If there are insufficient
    permissions to create the directory, log an error and return.
    """
    if not os.path.exists(folder):
        logger.debug(f"Creating folder {folder}")
        try:
            os.makedirs(folder)
        except OSError as e:
            if e.errno not in (errno.EACCES, errno.EEXIST):
                raise
            if e.errno == errno.EACCES:
                logger.error(f"Insufficient privileges to create folder {folder}.")
                return
    logger.debug(f"Folder {folder} already exists. Skipping creation.")

def get_folder(metadata):
    """
    Handles the logic to determine which folder this resource needs to be written to
    and returns it.
    It takes into account the FOLDER, FOLDER_ANNOTATION and the resource's annotations
    """
    folder = sidecar_settings.FOLDER

    # If there's no annotations, just return the original FOLDER immediately
    if 'annotations' not in metadata:
        return folder

    annotations = metadata['annotations']

    folder_annotation = sidecar_settings.FOLDER_ANNOTATION

    if folder_annotation in annotations:
        folder = annotations[folder_annotation]

    return folder

def get_filepath(filename, folder, kind, body):
    """
    Returns unique path if UNIQUE_FILENAMES are desired.
    Otherwise, simply returns the concatenated filename with the folder.
    """
    if sidecar_settings.UNIQUE_FILENAMES:
        namespace = 'default'
        if 'namespace' in body['metadata']:
            namespace = body['metadata']['namespace']

        name = body['metadata']['name']
        kind = kind.lower()

        filename = namespace + "." + kind + "_" + name + "." + filename

    return os.path.join(folder, filename)


def delete_file(body, kind, logger):
    folder = get_folder(body['metadata'])

    for filename in body['data'].keys():
        filepath = get_filepath(filename, folder, kind, body)
        logger.info(f"[DELETE:{kind}] Deleting file {filepath}.")
        try:
            os.remove(filepath)
        except FileNotFoundError:
            logger.error(f"[DELETE:{kind}] {filepath} not found.")
        except OSError as e:
            logger.error(e)

def write_file(event, body, kind, logger):
    """
    Write contents to the desired filepath if they have changed.
    """
    event = event.upper()

    #  folder = get_folder(body['metadata'])
    folder = get_folder(body.metadata)
    create_folder(folder, logger)

    for filename, content in body['data'].items():
        filepath = get_filepath(filename, folder, kind, body)

        if kind == 'Secret':
            content = get_base64_decoded(content)

        if os.path.exists(filepath):
            # Compare file contents with new ones so we don't update the file if nothing changed
            sha256_hash_new = hashlib.sha256(content.encode('utf-8'))
            with open(filepath, 'rb') as f:
                sha256_hash_cur = hashlib.sha256()
                for byte_block in iter(lambda: f.read(4096),b""):
                    sha256_hash_cur.update(byte_block)

            if sha256_hash_new.hexdigest() == sha256_hash_cur.hexdigest():
                logger.info(f"[{event}:{kind}] Contents of {filepath} haven't changed. Not overwriting existing file.")
                continue

        try:
            with open(filepath, 'w') as f:
                logger.info(f"[{event}:{kind}] Writing content to file {filepath}")
                f.write(content)
        # TODO: Flesh out IO exception handling here
        except Exception as e:
            logger.error(e)

        if sidecar_settings.DEFAULT_FILE_MODE:
            os.chmod(filepath, sidecar_settings.DEFAULT_FILE_MODE)
