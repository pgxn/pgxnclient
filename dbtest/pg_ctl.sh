#!/bin/bash
source env.sh

pg_ctl -D postgresql-${PG_VERSION}/data $1
