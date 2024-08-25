#!/bin/sh
# This script is designed to run tests for the protoconfloader project.
# It starts the protoconf agent in development mode, runs pytest with coverage,
# and then stops the protoconf agent.

pkill -9 protoconf >/dev/null 2>&1
protoconf agent -dev tests/test_data/. &
pytest --cov=protoconfloader tests/ 
pkill  -9 protoconf >/dev/null 2>&1

