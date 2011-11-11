export PG_VERSION=9.1.1
export PG_ROOT=`pwd`/postgresql-${PG_VERSION}/root/
export PG_PORT=15432
export PYTHONPATH=`pwd`/..:$PYTHONPATH
export PATH=`pwd`/../bin:${PG_ROOT}/bin/:${PATH}
export PGXN=`which pgxn`
