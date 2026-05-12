#!/usr/bin/env bash
set -e
python3 -m pip install --upgrade pip
pip install -r requirements.txt
python3 init_system.py
docker-compose up --build -d
printf "Deployment complete. Visit http://localhost:8000\n"
