#!/bin/bash

set -euo pipefail
# set -x

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$dir"

source env.sh

wget https://ftp.postgresql.org/pub/source/v${PG_VERSION}/postgresql-${PG_VERSION}.tar.bz2
tar xjvf postgresql-${PG_VERSION}.tar.bz2
rm postgresql-${PG_VERSION}.tar.bz2
cd postgresql-${PG_VERSION}
./configure --prefix=`pwd`/root
make
make install
`pwd`/root/bin/initdb -D data

set_param () {
    # Set a parameter in a postgresql.conf file
    param=$1
    value=$2

    sed -i "s/^\s*#\?\s*$param.*/$param = $value/" "data/postgresql.conf"
}

set_param port "${PG_PORT}"
set_param listen_addresses "'*'"
