#!/bin/bash

set -e

source .venv/bin/activate
.venv/bin/uvicorn app.main:app --reload