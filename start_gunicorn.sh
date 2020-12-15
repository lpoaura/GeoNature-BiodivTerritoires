#!/bin/bash
APP_DIR=$(readlink -e "${0%/*}")

. $APP_DIR/config/settings.ini


echo "Starting: $app_name"
echo "AppDir: $APP_DIR"
echo "Settings: $APP_DIR/config/settings.ini"

# activate the virtualenv
source $APP_DIR/venv/bin/activate

mkdir -p $APP_DIR/var/log/

cd $APP_DIR

gunicorn wsgi:app --error-log $APP_DIR/var/log/gn_errors.log --pid="${app_name:-gnbt}.pid" -w "${gun_num_workers:-4}" -t ${gun_timeout:-30} -b "${gun_host:-0.0.0.0}:${gun_port:-8080}"  -n "${app_name:-gnbt}"
