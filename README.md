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

## Configuration Environment Variables

| Variable             | Required?  | Default | Description                                                                                                                                                                                                                                                                      |
| -------------------- |:----------:|:-------:| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LABEL                | <b>Yes</b> | None    | Label that should be used for filtering                                                                                                                                                                                                                                          |
| FOLDER               | <b>Yes</b> | None    | Folder where the files should be placed.                                                                                                                                                                                                                                         |
| LABEL_VALUE          | No         | None    | The value for the label you want to filter your resources on.<br>Don't set a value to filter by any value                                                                                                                                                                        |
| NAMESPACE            | No         | 'ALL'   | The namespace from which resources will be watched.<br>If not set or set to `ALL`, it will watch all namespaces.                                                                                                                                                                 |
| DEFAULT_FILE_MODE    | No         | 644     | The default file system permission for every file. Use three digits (e.g. '500', '440', ...)                                                                                                                                                                                     |
| VERBOSE              | No         | False   | A value of 'true' will enable the kopf verbose logs                                                                                                                                                                                                                              |
| DEBUG                | No         | False   | A value of 'true' will enable the kopf debug logs                                                                                                                                                                                                                                |
| LIVENESS             | No         | True    | A value of 'false' will disable the kopf liveness probe                                                                                                                                                                                                                          |
| WATCH_CLIENT_TIMEOUT | No         | 660     | (seconds) is how long the session with a watching request will exist before closing it from the client side. This includes the connection establishing and event streaming.                                                                                                      |
| WATCH_SERVER_TIMEOUT | No         | 600     | (seconds) is how long the session with a watching request will exist before closing it from the server side. This value is passed to the server side in a query string, and the server decides on how to follow it. The watch-stream is then gracefully closed.                  |
| EVENT_LOGGING        | No         | False   | A value of 'true' will allow the operator to log directly to k8s events (`kubectl get events`).<br>Note that if you enable this, you'll need to provide the operator with RBAC access to `events` resources, see an example of how to do this in [rbac.yaml](examples/rbac.yaml) |                   |

## Gotchas

### Resource deletion

With the usage of k8s operators, we have access to [finalizers](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/#finalizers)

Finalizers allow controllers (which operators are a subset of) to perform given actions on a resource before it is garbage collected by Kubernetes.

Since we want `kopf-k8s-sidecar` to delete previously created files when a resource is removed, finalizers are added to ensure this task is performed by the operator.

If the operator is down, resources managed by it won't be able to be deleted.

To resolve this, simply restart the operator container or patch the finalizers out of the resource that you want to forcibly remove.

This is documented by [kopf](https://kopf.readthedocs.io/en/latest/troubleshooting/#kubectl-freezes-on-object-deletion) as well.