#!/bin/sh
set -o errexit #abort if any command fails

echo 'Installing dependencies'
pip install -r requirements-build.txt

echo 'Building site'
./build.py -q

touch _build/html/.nojekyll