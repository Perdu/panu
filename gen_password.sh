#!/bin/bash

function gen_pass() {
    < /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c12 ; echo
}

MARIADB_PASSWORD=$(gen_pass)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

sed -i "s/db_pass\s*=\s*.*/db_pass = ${MARIADB_PASSWORD}/" panu.conf.docker

ans=$(test -f .env && grep MARIADB_PASSWORD .env)
if [ $? -eq 0 ]
then
    sed -i "s/MARIADB_PASSWORD\s*=\s*.*/MARIADB_PASSWORD=${MARIADB_PASSWORD}/" .env    
else
    echo "MARIADB_PASSWORD=${MARIADB_PASSWORD}" > .env
fi
