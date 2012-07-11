#!/bin/bash
source env.sh

${PG_ROOT}/bin/pg_ctl -D postgresql-${PG_VERSION}/data $1
