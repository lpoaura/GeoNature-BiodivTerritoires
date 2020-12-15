#!/bin/bash

echo "|-------------------------------------------|"
echo "|               GeoNature                   |"
echo "|        Biodiversité des territoires       |"
echo "|-------------------------------------------|"


export DBHOST=${POSTGRES_HOST:-db}
export DBNAME=${POSTGRES_DB:-geonature}
export DBUSER=${POSTGRES_USER:-geonatuser}
export DBPWD=${POSTGRES_PASSWORD:-geonatpwd}
export DBPORT=${POSTGRES_PORT:-5432}
export SECRETKEY=${SECRETKEY:-$(< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c50)}
export SRID=${SRID:-4326}


function create_config {
    echo "Generate new config file"
    cp /app/configs/config.py.sample /config/config.py
    sed -i "s/dbHost/${DBHOST}/g" /config/config.py
    sed -i "s/dbName/${DBNAME}/g" /config/config.py
    sed -i "s/dbUser/${DBUSER}/g" /config/config.py
    sed -i "s/dbPassword/${DBPWD}/g" /config/config.py
    sed -i "s/dbPort/${DBPORT}/g" /config/config.py
    sed -i "s/secretKey/${SECRETKEY}/g" /config/config.py
    sed -i "s/2154/${SRID}/g" /config/config.py
    sed -i "s/taxhubUrl/${TAXHUB_URL}/g" /config/config.py
}


if [ ! -f /config/config.py ]; then
    create_config
else
    echo "config file already exists" 
    if $DEBUG; then
      echo "DEBUG mode, delete reinit config file"
      create_config
    fi
fi

rm /app/config.py
ln -s /config/config.py /app/config.py

ls -alh /app

until pg_isready -h $DBHOST -p $DBPORT
do
  echo "Awaiting Database container"
  sleep 1
done
sleep 2

cd /app

if $DEBUG; then
  echo "Debug mode"
  python -m wsgi
else 
  echo "Production mode"
  gunicorn wsgi:app --error-log - --access-logfile - --pid="${app_name:-gnbt}.pid" -w "${gun_num_workers:-4}" -t ${gun_timeout:-30} -b "${gun_host:-0.0.0.0}:${gun_port:-8080}"  -n "${app_name:-gnbt}"
fi
