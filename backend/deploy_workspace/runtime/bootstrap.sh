#!/bin/sh
echo "Container initialized by DevOpsForge"
test -f /app/data/.env && export $(cat /app/data/.env | xargs)
exec "$@"
