echo "INSTALL"
${PGXN} install --pg_config ${PG_CONFIG} ${LEVEL} ${EXTENSION} || exit

echo "CHECK"
${PGXN} check --pg_config ${PG_CONFIG} ${TEST_DSN} ${LEVEL} ${EXTENSION}

echo "LOAD/UNLOAD"
dropdb -h ${PG_HOST} -p ${PG_PORT} ${TEST_DB}
createdb -h ${PG_HOST} -p ${PG_PORT} ${TEST_DB}
${PGXN} load --pg_config ${PG_CONFIG} ${TEST_DSN} ${LEVEL} ${EXTENSION} || exit
${PGXN} unload --pg_config ${PG_CONFIG} ${TEST_DSN} ${LEVEL} ${EXTENSION}

echo "UNINSTALL"
dropdb -h ${PG_HOST} -p ${PG_PORT} ${TEST_DB}
${PGXN} uninstall --pg_config ${PG_CONFIG} ${LEVEL} ${EXTENSION} || exit

