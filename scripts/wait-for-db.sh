#!/bin/sh
set -e

host="$DB_HOST"
port="$DB_PORT"

echo "Esperando a que MySQL ($host:$port) esté disponible..."

while ! nc -z "$host" "$port"; do
  sleep 1
done

echo "MySQL está disponible, iniciando la aplicación..."
exec "$@"