import sidecar_settings

def label_is_satisfied(meta, **_):
    """Runs the logic for LABEL and LABEL_VALUE and tells us if we need to watch the resource"""

    # if there are no labels in the resource, there's no point in checking further
    if 'labels' not in meta:
        return False

    # If LABEL_VALUE wasn't set but we find the LABEL, that's good enough
    if sidecar_settings.LABEL_VALUE is None and sidecar_settings.LABEL in meta['labels'].keys():
        return True

    # If LABEL_VALUE was set, it needs to be the value of LABEL for one of the key-vars in the dict
    for key, value in meta['labels'].items():
        if key == sidecar_settings.LABEL and value == sidecar_settings.LABEL_VALUE:
            return True

    return False

def resource_is_desired(body, **_):
    """Runs the logic for the RESOURCE environment variable"""
    kind = body['kind'].lower()

    return sidecar_settings.RESOURCE in (kind, 'both')

def resource_is_cru(event, **_):
    """Returns true if the resource was created, resumed or updated in the on.event handler"""
    return not resource_is_deleted(event)

def resource_is_deleted(event, **_):
    """Returns true if the resource was deleted in the on.event handler"""
    return event['type'] == 'DELETED'
