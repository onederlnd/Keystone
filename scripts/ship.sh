#!/bin/bash

set -e

# pytest tests/ -v || exit 1
# echo "== TESTS COMPLETE =="

git add .
git commit -m "${1:-update}"
git push

echo "== PUSH COMPLETE =="