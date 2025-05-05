#!/usr/bin/env bash
# wait-for-it.sh

host="$1"
port="$2"
shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "Postgres is unavailable - waiting..."
  sleep 1
done

>&2 echo "db is up - executing command"
exec $cmd
