#!/bin/bash
source env.sh
export EXTENSION=s3_fdw
export LEVEL=--unstable
source _test_template.sh
