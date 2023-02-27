FROM python:3.11 as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS python-deps

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Install python dependencies in /.venv directly from the lock file for reproducible builds
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --ignore-pipfile --deploy

FROM python:3.11-alpine3.15 AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
# RUN useradd --create-home appuser
# WORKDIR /home/appuser
# USER appuser

# Install application into container
COPY app/ .

COPY ./docker-entrypoint.sh .
ENTRYPOINT ["./docker-entrypoint.sh"]

# Use the nobody user's numeric UID/GID to satisfy MustRunAsNonRoot PodSecurityPolicies
# https://kubernetes.io/docs/concepts/policy/pod-security-policy/#users-and-groups
# IMPORTANT: This user can be overriden by a k8s SecurityContext!
USER 65534:65534

CMD ["kopf-k8s-sidecar"]
