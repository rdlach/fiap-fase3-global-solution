#!/bin/sh
set -eu

if [ "$#" -ne 1 ] || [ ! -f "$1/index.html" ]; then
    echo "Uso: ./publicar.sh /pasta/que/contem/index.html" >&2
    exit 1
fi

bucket=$(terraform output -raw bucket)
distribuicao=$(terraform output -raw distribution_id)
aws s3 sync "$1/" "s3://$bucket/" --no-follow-symlinks
aws cloudfront create-invalidation --distribution-id "$distribuicao" --paths '/*'
terraform output -raw site_url
printf '\n'
