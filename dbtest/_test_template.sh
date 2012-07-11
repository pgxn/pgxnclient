echo "INSTALL"
${PGXN} install ${LEVEL} ${EXTENSION} || exit

echo "CHECK"
${PGXN} check ${TEST_DSN} ${LEVEL} ${EXTENSION}

echo "LOAD/UNLOAD"
dropdb -h ${PG_HOST} -p ${PG_PORT} ${TEST_DB}
createdb -h ${PG_HOST} -p ${PG_PORT} ${TEST_DB}
${PGXN} load ${TEST_DSN} ${LEVEL} ${EXTENSION} || exit
${PGXN} unload ${TEST_DSN} ${LEVEL} ${EXTENSION}

echo "UNINSTALL"
dropdb -h ${PG_HOST} -p ${PG_PORT} ${TEST_DB}
${PGXN} uninstall ${LEVEL} ${EXTENSION} || exit

