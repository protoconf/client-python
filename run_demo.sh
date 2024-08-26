#!/bin/sh
# This script is used to run the demo application.
# It starts the protoconf agent, which is responsible for managing the configuration.
# Then it starts the demo application, which uses the protoconf agent to dynamically update its configuration.
# Finally, it stops the protoconf agent after the demo application has finished running.
export PYTHONPATH=$PYTHONPATH:$(pwd)/tests
pkill -9 protoconf >/dev/null 2>&1
protoconf agent -dev tests/test_data/. &
python demo_app/demo_app.py
pkill -9 protoconf >/dev/null 2>&1
