#!/bin/bash

set -euo pipefail
set -x

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$dir"

source env.sh
export EXTENSION=semver
source _test_template.sh
