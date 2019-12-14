#!/bin/sh

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


shopt -s dotglob nullglob

if [ ! -f /config/config.py ]; then
    echo "Generate new config file"
    cp configs/config.py.sample /config/config.py
    ln -s /config/config.py /app/config.py
    sed -i "s/dbHost/${DBHOST}/g" /config/config.py
    sed -i "s/dbName/${DBNAME}/g" /config/config.py
    sed -i "s/dbUser/${DBUSER}/g" /config/config.py
    sed -i "s/dbPassword/${DBPWD}/g" /config/config.py
    sed -i "s/dbPort/${DBPORT}/g" /config/config.py
    sed -i "s/secretKey/${SECRETKEY}/g" /config/config.py
else
    echo "config file already exists" 
fi

python -m run