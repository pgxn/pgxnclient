#!/bin/bash

set -euo pipefail
# set -x

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$dir"

source env.sh

${PG_ROOT}/bin/pg_ctl -D "${dir}/postgresql-${PG_VERSION}/data" $1
