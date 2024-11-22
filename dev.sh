#!/bin/bash

prompt_for_input() {
    local var_name=$1
    local prompt_message=$2
    local default_value=$3

    read -p "$prompt_message [$default_value]: " input_value
    if [ -z "$input_value" ]; then
        eval "$var_name='$default_value'"
    else
        eval "$var_name='$input_value'"
    fi
}


prepare_env_files() {
    echo "Preparing environment files..."

    # Prepare postgres password file
    if [ -f ./env/postgres_knyfe_password ]; then
        echo "Postgresql password file already exists. Skipping..."
    else
        echo "Generating Postgresql password file..."
        mkdir -p ./env
        openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32 > ./env/postgres_knyfe_password
    fi

    # Prepare postgres.env file
    if [ -f ./env/postgres.env ]; then
        echo "Postgresql environment file already exists. Skipping..."
    else
        echo "Creating Postgresql environment file..."
        # allow customizing the database name and user
        prompt_for_input DB_NAME "Enter the database name" "knyfe"
        prompt_for_input DB_USER "Enter the database user" "knyfe_rw"
        cat <<EOF > ./env/postgres.env
POSTGRES_USER=$DB_USER
POSTGRES_DB=$DB_NAME
POSTGRES_PASSWORD_FILE=/run/secrets/postgres_knyfe_password
EOF
    fi

    # Prepare django.env file
    if [ -f ./env/knyfe.env ]; then
        echo "Django environment file already exists. Skipping..."
    else
        echo "Creating Django environment file..."
        DB_PASSWORD=$(cat ./env/postgres_knyfe_password)
        DJANGO_SECRET_KEY=$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 50)
        cat <<EOF > ./env/knyfe.env
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
DB_USER=$DB_USER
DB_NAME=$DB_NAME
DB_PASSWORD=$DB_PASSWORD
DB_HOST=postgres
DB_PORT=5432
EOF
    fi

    echo "Environment files prepared."
}

# if no arguments are provided, print usage
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <subcommand> [args]"
  exit 1
fi

subcommand=$1
shift

echo "Executing $subcommand with arguments: $@"

case "$subcommand" in
    build)
        prepare_env_files
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
