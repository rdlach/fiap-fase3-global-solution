#!/bin/sh
set -eu
cd "$(dirname "$0")"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
if [ "${1:-}" = "--local" ]; then
    mkdir -p "$tmp/pyhtml-beta/src" "$tmp/pyhtml-beta/dados"
    cp ../../pyhtml-beta/index.html ../../pyhtml-beta/style.css "$tmp/pyhtml-beta/"
    cp ../../pyhtml-beta/src/*.py "$tmp/pyhtml-beta/src/"
    for arquivo in bairros_sp.csv distritos_sp.csv ocorrencias_exemplo.csv; do
        cp "../../pyhtml-beta/dados/$arquivo" "$tmp/pyhtml-beta/dados/"
    done
else
    git -C ../.. archive origin/main pyhtml-beta | tar -xf - -C "$tmp"
fi
cp jose/adapter.py "$tmp/pyhtml-beta/"
dest="$PWD/jose.zip"
rm -f "$dest"
(cd "$tmp/pyhtml-beta" && zip -q -r "$dest" adapter.py src dados index.html style.css)
