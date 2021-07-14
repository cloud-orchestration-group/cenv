#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

ZIMAGI_DEFAULT_RUNTIME_REPO="${ZIMAGI_DEFAULT_RUNTIME_REPO:-registry.hub.docker.com}"
ZIMAGI_DEFAULT_RUNTIME_IMAGE="${ZIMAGI_DEFAULT_RUNTIME_IMAGE:-zimagi/zimagi:latest}"

if [ -f /var/local/zimagi/zimagi.env ]
then
    source /var/local/zimagi/zimagi.env

    if [ -z "${ZIMAGI_RUNTIME_IMAGE}" ]
    then
        ZIMAGI_RUNTIME_IMAGE="${ZIMAGI_BASE_IMAGE}"
    fi
else
    ZIMAGI_REPO="${ZIMAGI_DEFAULT_RUNTIME_REPO}"
    ZIMAGI_RUNTIME_IMAGE="${ZIMAGI_DEFAULT_RUNTIME_IMAGE}"
fi

if ! docker inspect "${ZIMAGI_RUNTIME_IMAGE}" >/dev/null 2>&1
then
    rm -f /var/local/zimagi/zimagi.env
    ZIMAGI_RUNTIME_IMAGE="${ZIMAGI_DEFAULT_RUNTIME_IMAGE}"
fi
docker run --rm --interactive --tty \
    --env "ZIMAGI_CLI_EXEC=True" \
    --env-file /var/local/zimagi/.env \
    --env-file <(env | grep "ZIMAGI_") \
    --network host \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /usr/local/share/zimagi:/usr/local/share/zimagi \
    --volume /var/local/zimagi:/var/local/zimagi \
    --volume /usr/local/lib/zimagi:/usr/local/lib/zimagi \
    "${ZIMAGI_RUNTIME_IMAGE}" "${@}"
