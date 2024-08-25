#!/bin/sh
# This script generates Python code from the protoconf_service.proto file.
# It uses the grpc_tools.protoc module to compile the .proto file into Python code.
# The generated code is saved in the same directory as the .proto file.
python -m grpc_tools.protoc  -I. --python_out=. --grpc_python_out=.  agent/api/proto/v1/protoconf_service.proto  