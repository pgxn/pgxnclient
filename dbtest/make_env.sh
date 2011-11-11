#!/bin/bash
source env.sh

wget http://wwwmaster.postgresql.org/redir/170/h/source/v${PG_VERSION}/postgresql-9.1.1.tar.bz2
tar xjvf postgresql-${PG_VERSION}.tar.bz2
rm postgresql-${PG_VERSION}.tar.bz2
cd postgresql-${PG_VERSION}
./configure --prefix=`pwd`/root
make
make install
./root/bin/initdb -D data
sed -e "s/#port = 5432/port = ${PG_PORT}/" postgresql-${PG_VERSION}/data/postgresql.conf \
    | sponge postgresql-{PG_VERSION}/data/postgresql.conf

