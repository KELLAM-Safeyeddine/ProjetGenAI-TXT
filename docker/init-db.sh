#!/bin/sh
set -eu
if [ ! -s /run/db-secrets/postgres-password ]; then
    umask 027
    head -c 48 /dev/urandom | base64 > /run/db-secrets/postgres-password
    chgrp 10001 /run/db-secrets/postgres-password
    chmod 640 /run/db-secrets/postgres-password
fi
exec docker-entrypoint.sh postgres
