source env.sh

echo "INSTALL"
${PGXN} install --nosudo ${EXTENSION} || exit
echo "CHECK"
${PGXN} check -p ${PG_PORT} ${EXTENSION} || exit
dropdb -p ${PG_PORT} contrib_regression
echo "UNINSTALL"
${PGXN} uninstall --nosudo ${EXTENSION} || exit

