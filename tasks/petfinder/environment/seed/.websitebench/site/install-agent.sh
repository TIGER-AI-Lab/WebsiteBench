#!/usr/bin/env bash
set -Eeuo pipefail

python -m pip install --no-cache-dir \
  argon2-cffi==25.1.0 \
  fastapi==0.139.2 \
  jinja2==3.1.6 \
  python-multipart==0.0.32 \
  uvicorn==0.51.0
