#!/bin/bash

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <subcommand> [args]"
  exit 1
fi

subcommand=$1
shift

echo "Executing $subcommand with arguments: $@"

case "$subcommand" in
  build)
    docker compose up -d --build
    ;;
  remove)
    docker compose down &&
    docker volume rm knyfe_postgres_knyfe_data
    ;;
  test)
    docker compose exec knyfe manage.py test $@
    ;;
  manage.py)
    docker compose exec knyfe manage.py $@
    ;;
  *)
    echo "Unknown subcommand: $subcommand"
    exit 1
    ;;
esac
