#!/bin/bash
echo ""
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo ""
echo "   .|||||||||.          .|||||||||."
echo "  |||||||||||||        |||||||||||||"
echo " |||||||||||' .\      /. '|||||||||||"
echo " '||||||||||_,__o    o__,_||||||||||'"
echo ""
echo " > GeoNature"
echo " > Biodiversité des territoires"
echo " > https://github.com/lpoaura/GeoNature-BiodivTerritoires"
echo ""
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo ""

until [ "$(psql $(python -c 'print("'$SQLALCHEMY_DATABASE_URI'".replace("+psycopg2",""))') -XtAc "SELECT 1")" = '1' ]; do
  echo "Awaiting Database container"
  sleep 1
done
sleep 2

cd /app

echo "DEBUG: $DEBUG"

if [ "$DEBUG" = true ]; then
  echo "Debug mode"
  python -m wsgi
else
  echo "Production mode"
  gunicorn wsgi:app --error-log - --access-logfile - --pid="${app_name:-gnbt}.pid" -w "${gun_num_workers:-4}" -t ${gun_timeout:-30} -b "${gun_host:-0.0.0.0}:${gun_port:-8080}" -n "${app_name:-gnbt}"
fi
