export PG_VERSION=11.2
export PG_ROOT=`pwd`/postgresql-${PG_VERSION}/root/
export PATH=${PG_ROOT}/bin/:${PATH}
export PG_PORT=15432
export PG_HOST=localhost
export TEST_DB=contrib_regression
export TEST_DSN="-d ${TEST_DB} -h ${PG_HOST} -p ${PG_PORT}"
export LEVEL=""

# find the pgxn version to be tested
# export PYTHONPATH=`pwd`/..:$PYTHONPATH
# export PATH=`pwd`/../bin:${PATH}
export PGXN=`which pgxn`
