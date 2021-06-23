# kopf-k8s-sidecar

## What is this?

An implementation of [k8s-sidecar](https://github.com/kiwigrid/k8s-sidecar) using [kopf](https://github.com/nolar/kopf), an Python-based framework for kubernetes operators.

## Why?

At the moment of writing this documentation, there is an [issue](https://github.com/kiwigrid/k8s-sidecar/issues/85) with `k8s-sidecar` where it will "hang" after a short amount of time while watching for resources.

Upon inspecting the codebase for the issue, I soon concluded that much of the logic could be drastically simplified by using an operator framework.

Initially, I considered using [operator-sdk](https://github.com/operator-framework/operator-sdk) but I'm not a huge fan of Go.

Additionally, I hope to contribute this rewrite to `k8s-sidecar` at some point and I figured that keeping things in Python would ease that transition significantly.

## How does it work?

In essence, it works the same way as the original `k8s-sidecar` does.

In its most minimal form, it will look for a defined `LABEL` in a `ConfigMap` and/or `Secret` and write the contents defined in their `data` field to a given `FOLDER` in a file.

## Quickstart

To see `kopf-k8s-sidecar` in action, I recommend deploying the resources located in `/examples` to your k8s cluster.

Once that's done, you can view the `sidecar` container logs to view events happen as you create, delete or update `ConfigMap`s or `Secret`s.

Similarly, you can view the `bash` container logs to see how the files defined by your `ConfigMap`s and `Secret`s are populated there.

## Dockerhub

All tags are automatically built and pushed to [Dockerhub](https://hub.docker.com/r/omegavveapon/kopf-k8s-sidecar).

## Grafana Helm Chart users

If you are looking to use this image with the [Grafana Helm chart](https://github.com/grafana/helm-charts/tree/main/charts/grafana), then this is the section for you.

### Sidecar image

* Set `.Values.sidecar.image.repository` to `omegavveapon/kopf-k8s-sidecar` 
* Set `.Values.sidecar.image.tag` to the latest tag in [Releases](https://github.com/OmegaVVeapon/kopf-k8s-sidecar/releases)

### RBAC permissions

Provide `patch` permissions for `configmaps` and `secrets` in the `values.yaml`

```
rbac:
-  extraClusterRoleRules: []
+  extraClusterRoleRules:
+    - apiGroups: [""]  # "" indicates the core API group
+      resources: ["configmaps", "secrets"]
+      verbs: ["patch"]
```
The operator needs to `patch` resources to add a `kopf.zalando.org/last-handled-configuration` annotation which is used to handle [change detection](https://kopf.readthedocs.io/en/stable/configuration/?highlight=last-handled-configuration#change-detection).

## Configuration Environment Variables

| Variable | Required? | Default | Description |
| --- |:---:|:---:| --- |
| LABEL | <b>Yes</b> | `None` | Label that should be used for filtering |
| FOLDER | <b>Yes</b> | `None` | Folder where the files should be placed. |
| FOLDER_ANNOTATION | No | `k8s-sidecar-target-directory` | The annotation the sidecar will look for in `ConfigMap`s and/or `Secret`s to override the destination folder for files |
| LABEL_VALUE | No | `None` | The value for the label you want to filter your resources on.<br>Don't set a value to filter by any value |
| NAMESPACE | No | `ALL` | The `Namespace`(s) from which resources will be watched. <br>For multiple namespaces, use a comma-separated string like "default,test".<br>If not set or set to `ALL`, it will watch all `Namespace`s. |
| RESOURCE | No | `configmap` | The resource type that the operator will filter for. Can be `configmap`, `secret` or `both` |
| METHOD | No | `WATCH` | Determines how kopf-k8s-sidecar will run. If `WATCH` it will run like like a normal operator **forever**. <br>If `LIST` it will gather the matching configmaps and secrets currently present, write those files to the destination directory and **die** |
| DEFAULT_FILE_MODE | No | `None` | The default file system permission for every file. Use three digits (e.g. '500', '440', ...) |
| DEBUG | No | `False` | A value of `true` will enable the kopf debug logs |
| WATCH_CLIENT_TIMEOUT | No | `660` | (seconds) is how long the session with a watching request will exist before closing it from the client side. This includes the connection establishing and event streaming. |
| WATCH_SERVER_TIMEOUT | No | `600` | (seconds) is how long the session with a watching request will exist before closing it from the server side. This value is passed to the server side in a query string, and the server decides on how to follow it. The watch-stream is then gracefully closed. |
| UNIQUE_FILENAMES | No (but recommended!) | `False` | A value of `true` will produce unique filenames to avoid issues when duplicate data keys exist between `ConfigMap`s and/or `Secret`s within the same or multiple `Namespace`s. |

## Gotchas

### Namespaces

Contrary to the original k8s-sidecar, we will look in `ALL` namespaces by default as documented in the [Configuration Environment Variables](#configuration-environment-variables) section.

If you only want to look for resources in the namespace where the sidecar is installed, feel free to specify it.
