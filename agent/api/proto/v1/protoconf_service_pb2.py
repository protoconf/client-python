# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: agent/api/proto/v1/protoconf_service.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n*agent/api/proto/v1/protoconf_service.proto\x12\x0cprotoconf.v1\x1a\x19google/protobuf/any.proto\"P\n\x19\x43onfigSubscriptionRequest\x12\x0c\n\x04path\x18\x01 \x01(\t\x12\x0f\n\x07\x63hannel\x18\x02 \x01(\t\x12\x14\n\x0cservice_name\x18\x03 \x01(\t\"B\n\x0c\x43onfigUpdate\x12#\n\x05value\x18\x01 \x01(\x0b\x32\x14.google.protobuf.Any\x12\r\n\x05\x65rror\x18\x02 \x01(\t2o\n\x10ProtoconfService\x12[\n\x12SubscribeForConfig\x12\'.protoconf.v1.ConfigSubscriptionRequest\x1a\x1a.protoconf.v1.ConfigUpdate0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'agent.api.proto.v1.protoconf_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CONFIGSUBSCRIPTIONREQUEST']._serialized_start=87
  _globals['_CONFIGSUBSCRIPTIONREQUEST']._serialized_end=167
  _globals['_CONFIGUPDATE']._serialized_start=169
  _globals['_CONFIGUPDATE']._serialized_end=235
  _globals['_PROTOCONFSERVICE']._serialized_start=237
  _globals['_PROTOCONFSERVICE']._serialized_end=348
# @@protoc_insertion_point(module_scope)
