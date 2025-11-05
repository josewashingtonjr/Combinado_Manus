#!/bin/bash
cd /home/ubuntu/projeto
export FLASK_ENV=development
export FLASK_RUN_PORT=5001
python3.11 app.py
