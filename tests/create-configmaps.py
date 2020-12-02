from configargparse import RawTextHelpFormatter, ArgParser
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

parser = ArgParser(formatter_class=RawTextHelpFormatter)
parser.add('--amount', required=False, default=1, help='Amount of ConfigMap objects to create')
parser.add('-n', '--namespace', required=False, default='default', help='Namespace on which ConfigMaps will be created')
parser.add('-l', '--label', required=False, default='findme', help='Label to inject for the k8s-sidecar to filter')
parser.add('-v', '--value', required=False, default='yea', help='Label value to inject for the k8s-sidecar to filter')
args = parser.parse_args()

DEFAULT_CONFIGMAP_NAME = 'load-test'

v1 = client.CoreV1Api()

for current in range(1, int(args.amount)+1):
    name = f"{DEFAULT_CONFIGMAP_NAME}-{current}"
    print(f"Creating ConfigMap {name} in the {args.namespace} namespace...")

    data = {
        name: f"These are the contents for file {name}"
    }

    metadata = client.V1ObjectMeta(
        name=name,
        labels={
            args.label: args.value
        }
    )

    body = client.V1ConfigMap(data=data, metadata=metadata)
    try:
        api_response = v1.create_namespaced_config_map(args.namespace, body)
    except ApiException as e:
        print("Exception when calling CoreV1Api->create_namespaced_config_map: %s\n" % e)
