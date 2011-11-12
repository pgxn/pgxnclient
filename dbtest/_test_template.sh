echo "INSTALL"
${PGXN} install --nosudo ${LEVEL} ${EXTENSION} || exit

echo "CHECK"
${PGXN} check ${TEST_DSN} ${LEVEL} ${EXTENSION}

echo "UNINSTALL"
dropdb -p ${PG_PORT} ${TEST_DB}
${PGXN} uninstall --nosudo ${LEVEL} ${EXTENSION} || exit

