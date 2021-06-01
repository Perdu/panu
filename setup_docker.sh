#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

cp panu.conf panu.conf.docker

sed -i "s/db_server\s*=\s*.*/db_server = db/" panu.conf.docker
sed -i "s/db_name\s*=\s*.*/db_name = panu/" panu.conf.docker
sed -i "s/db_user\s*=\s*.*/db_user = panu/" panu.conf.docker

./gen_password.sh
