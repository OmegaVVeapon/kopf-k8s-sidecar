import os
from misc import get_required_env_var

def label_is_satisfied(meta, **_):
    """Runs the logic for LABEL and LABEL_VALUE and tells us if we need to watch the resource"""
    label = get_required_env_var('LABEL')
    label_value = os.getenv('LABEL_VALUE')

    # if there are no labels in the resource, there's no point in checking further
    if 'labels' not in meta:
        return False

    # If LABEL_VALUE wasn't set but we find the LABEL, that's good enough
    if label_value is None and label in meta['labels'].keys():
        return True

    # If LABEL_VALUE was set, it needs to be the value of LABEL for one of the key-vars in the dict
    for key, value in meta['labels'].items():
        if key == label and value == label_value:
            return True

    return False

def resource_is_desired(body, **_):
    """Runs the logic for the RESOURCE environment variable"""
    resource = os.getenv('RESOURCE', 'configmap')

    kind = body['kind'].lower()

    return resource in (kind, 'both')

def resource_is_deleted(event, **_):
    """Returns true if the resource was deleted in the on.event handler"""
    return event['type'] == 'DELETED'
