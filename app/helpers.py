import os
import sys
import errno
import hashlib
from pathlib import Path

def print_stuff(event, body, logger):
    for filename, content in body['data'].items():
        logger.info(f"[{event.upper()}:{body['kind']}] {filename} = {content}")

def require_envvar(name):
    try:
        return os.environ[name]
    except KeyError:
        print(f"{name} environment variable is required! Exiting.")
        sys.exit(1)

def delete_file(body, folder, logger):
    for filename in body['data'].keys():
        filepath = os.path.join(folder, filename)
        logger.info(f"[DELETE:{body['kind']}] Deleting file {filepath}")
        try:
            os.remove(filepath)
        except FileNotFoundError:
            logger.error(f"[DELETE:{body['kind']}] {filepath} not found")
        except OSError as e:
            logger.error(e)

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

def write_file(event, folder, body, logger):
    """
    Write contents to the desired filepath if they have changed.
    """
    for filename, content in body['data'].items():
        filepath = os.path.join(folder, filename)

        if os.path.exists(filepath):
            # Compare file contents with new ones so we don't update the file if nothing changed
            sha256_hash_new = hashlib.sha256(content.encode('utf-8'))
            with open(filepath, 'rb') as f:
                sha256_hash_cur = hashlib.sha256()
                for byte_block in iter(lambda: f.read(4096),b""):
                    sha256_hash_cur.update(byte_block)

            if sha256_hash_new.hexdigest() == sha256_hash_cur.hexdigest():
                logger.info(f"[{event.upper()}:{body['kind']}] Contents of {filename} haven't changed. Not overwriting existing file")
                continue

        try:
            with open(filepath, 'w') as f:
                logger.info(f"[{event.upper()}:{body['kind']}] Writing content to file {filepath}")
                f.write(content)
        except Exception as e:
            logger.error(e)

        if os.getenv('DEFAULT_FILE_MODE'):
            mode = int(os.getenv('DEFAULT_FILE_MODE'), base=8)
            os.chmod(filepath, mode)

#  def uniqueFilename(filename, namespace, resource, resource_name):
#      """Return a unique filename derived from the arguments provided, e.g.
#      "namespace_{namespace}.{configmap|secret}_{resource_name}.{filename}".

#      This is used where duplicate data keys may exist between ConfigMaps
#      and/or Secrets within the same or multiple Namespaces.

#      Keyword arguments:
#      filename -- the filename derived from a data key present in a ConfigMap or Secret.
#      namespace -- the Namespace from which data is sourced.
#      resource -- the resource type, e.g. "configmap" or "secret".
#      resource_name -- the name of the "configmap" or "secret" resource instance.
#      """
#      return "namespace_" + namespace + "." + resource + "_" + resource_name + "." + filename

#  def request(url, method, payload=None):
#      retryTotal = 5 if os.getenv("REQ_RETRY_TOTAL") is None else int(os.getenv("REQ_RETRY_TOTAL"))
#      retryConnect = 5 if os.getenv("REQ_RETRY_CONNECT") is None else int(
#          os.getenv("REQ_RETRY_CONNECT"))
#      retryRead = 5 if os.getenv("REQ_RETRY_READ") is None else int(os.getenv("REQ_RETRY_READ"))
#      retryBackoffFactor = 0.2 if os.getenv("REQ_RETRY_BACKOFF_FACTOR") is None else float(
#          os.getenv("REQ_RETRY_BACKOFF_FACTOR"))
#      timeout = 10 if os.getenv("REQ_TIMEOUT") is None else float(os.getenv("REQ_TIMEOUT"))

#      username = os.getenv("REQ_USERNAME")
#      password = os.getenv("REQ_PASSWORD")
#      if username and password:
#          auth = (username, password)
#      else:
#          auth = None

#      r = requests.Session()
#      retries = Retry(total=retryTotal,
#                      connect=retryConnect,
#                      read=retryRead,
#                      backoff_factor=retryBackoffFactor,
#                      status_forcelist=[500, 502, 503, 504])
#      r.mount("http://", HTTPAdapter(max_retries=retries))
#      r.mount("https://", HTTPAdapter(max_retries=retries))
#      if url is None:
#          print(f"{timestamp()} No url provided. Doing nothing.")
#          return

#      # If method is not provided use GET as default
#      if method == "GET" or not method:
#          res = r.get("%s" % url, auth=auth, timeout=timeout)
#      elif method == "POST":
#          res = r.post("%s" % url, auth=auth, json=payload, timeout=timeout)
#          print(f"{timestamp()} {method} request sent to {url}. "
#                f"Response: {res.status_code} {res.reason} {res.text}")
#      return res
