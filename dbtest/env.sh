export PG_VERSION=9.1.1
export PG_ROOT=`pwd`/postgresql-${PG_VERSION}/root/
export PATH=${PG_ROOT}/bin/:${PATH}
export PG_PORT=15432
export PG_HOST=localhost
export TEST_DB=contrib_regression
export TEST_DSN="-d ${TEST_DB} -h ${PG_HOST} -p ${PG_PORT}"

# find the pgxn version to be tested
export PYTHONPATH=`pwd`/..:$PYTHONPATH
export PATH=`pwd`/../bin:${PATH}
export PGXN=`which pgxn`
