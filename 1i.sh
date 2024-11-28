#!/bin/bash
source venv/bin/activate
export FLASK_APP=iflexgpt.py
/home/max/.pyenv/shims/flask run -h 0.0.0.0 -p 5001
