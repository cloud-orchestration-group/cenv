#
#=========================================================================================
# Docker Utilities
#

function build_image () {
  SKIP_BUILD=${1:-0}

  debug "Function: build_image"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"

  info "Generating certificate environment ..."
  build_environment

  info "Setting up Zimagi package ..."
  cp -f "${__zimagi_app_dir}/VERSION" "${__zimagi_package_dir}/VERSION"

  info "Building Zimagi application image ..."
  find "${__zimagi_dir}" -name *.pyc -exec rm -f {} \;

  if [ -d "${__zimagi_data_dir}/run" ]; then
    find "${__zimagi_data_dir}/run" -type f -exec rm -f {} \;
  fi
  if [ $SKIP_BUILD -ne 1 ]; then
    docker build --force-rm --no-cache \
      --file $ZIMAGI_DOCKER_FILE \
      --tag $ZIMAGI_DEFAULT_RUNTIME_IMAGE \
      --build-arg ZIMAGI_CA_KEY \
      --build-arg ZIMAGI_CA_CERT \
      --build-arg ZIMAGI_KEY \
      --build-arg ZIMAGI_CERT \
      --build-arg ZIMAGI_DATA_KEY \
      "${__zimagi_dir}"
  fi
}

function docker_runtime_image () {
  if [ -f "${__zimagi_cli_env_file}" ]
  then
    source "${__zimagi_cli_env_file}"

    if [ -z "$ZIMAGI_RUNTIME_IMAGE" ]
    then
      ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_BASE_IMAGE"
    fi
  else
    ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
  fi

  if ! docker inspect "$ZIMAGI_RUNTIME_IMAGE" >/dev/null 2>&1
  then
    rm -f "${__zimagi_cli_env_file}"
    ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
  fi
  export ZIMAGI_RUNTIME_IMAGE
}
