#!/bin/sh
# This script is designed to run tests for the protoconfloader project.
# It starts the protoconf agent in development mode, runs pytest with coverage,
# and then stops the protoconf agent.
export PYTHONPATH=$PYTHONPATH:$(pwd)
pkill -9 protoconf >/dev/null 2>&1
protoconf agent -dev tests/test_data/. &
#pytest --cov=protoconfloader tests/ 
python -m pytest -s  
pkill  -9 protoconf >/dev/null 2>&1

