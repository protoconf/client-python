import logging
import pathlib
import inotify.constants
from typing import Any, Callable
from google.protobuf.any_pb2 import Any
from protoconf_pb2_grpc import ProtoconfServiceStub
import asyncio
import json
import os
import threading
import agent.api.proto.protoconf_service_pb2_grpc as pb
import grpc

import inotify.adapters
from agent.api.proto.protoconf_service_pb2 import ConfigSubscriptionRequest
from google.protobuf.json_format import Parse


AGENTDEFAULTADDRESS = "localhost:4300"


class Configuration:
    """
    The `Configuration` class is designed to manage and monitor configuration
    files for changes.
    It loads configuration data from a specified file, watches for changes both
    locally and via a gRPC service,
    and updates the configuration accordingly. It also allows for a callback
    function to be executed whenever the configuration changes.
    """

    def __init__(self, message: Any, service_name: str, logger: logging.Logger) -> None:
        """
        Initializes the configuration with the given message and service name.
        """
        self.message = message
        self.service_name = service_name
        self.logger = logging.getLogger()
        self.is_loaded = False
        self.is_watching_file = False
        self.is_watching_agent = False
        self.config_path = None
        self.config_file = None
        self.lock = asyncio.Lock()
        self.on_config_change_callback = None
        self.agent_address = AGENTDEFAULTADDRESS

    def set_logger(self, logger: logging.Logger) -> None:
        """
        Sets the logger for this configuration.
        """
        self.logger = logger

    def load_config(self, service_name: str, config_name: str) -> None:
        """
        Loads the configuration from the specified file.
        """
        if self.is_loaded:
            return
        self.service_name = service_name
        self.config_file = config_name
        try:
            self.__load_config()
            self.is_loaded = True
        except FileNotFoundError as e:
            self.logger.error(f"Config file not found: {e}")

    def __load_config(self) -> None:
        """
        Internal method to load and parse the configuration file.
        """
        try:
            with open(
                pathlib.Path(self.service_name) / self.config_file,
                "r",
                encoding="utf-8",
            ) as f:
                config_data = json.load(f)
                with self.lock:
                    self.message = Parse(json.dumps(config_data), self.message)
                if self.on_config_change_callback is not None:
                    self.on_config_change_callback(self.message)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Error decoding JSON: {e}") from None

    def on_config_change(self, cb: Callable) -> None:
        """
        Sets a callback function to be called when the configuration changes.
        """
        self.on_config_change_callback = cb

    async def __listen_to_changes(self, path: str) -> None:
        """
        Listens for configuration updates via a gRPC service.
        """
        self.logger.info(f"Listening to changes for {path}")
        try:
            with grpc.insecure_channel(self.agent_address) as channel:
                client = ProtoconfServiceStub(channel)
                request = ConfigSubscriptionRequest(path=path)
                for config_update in client.SubscribeForConfig(request):
                    with self.lock:
                        config_update.value.Unpack(self.message)
                    if self.on_config_change is not None:
                        self.on_config_change(self.message)
        except grpc.RpcError as e:
            self.logger.error(f"Error with gRPC communication: {e}")

    async def _file_watcher(self, delay: int = 0) -> None:
        """
        Watches the configuration file for changes and reloads it if modified.
        """
        self.logger.info("Starting watching config file")
        i = inotify.adapters.Inotify()
        i.add_watch(self.service_name, inotify.constants.IN_MODIFY)
        await asyncio.sleep(delay)
        for event in i.event_gen(yield_nones=False):
            (_, _, _, filename) = event
            await asyncio.sleep(0)
            if filename == self.config_file:
                try:
                    self.__load_config()
                    await asyncio.sleep(delay)
                except Exception as e:
                    self.logger.error(f"Error loading config: {e}")

    async def watch_config(self, delay: int = 0) -> None:
        """
        Starts both the file watcher and gRPC listener tasks with exception handling.
        """
        try:
            async with asyncio.TaskGroup() as tg:
                task1 = tg.create_task(self.__listen_to_changes(self.service_name))
                task2 = tg.create_task(self._file_watcher(delay))

            self.logger.info(
                f"Both tasks have completed now: {task1.result()}, {task2.result()}"
            )
        except Exception as e:
            self.logger.error(f"Error in watch_config: {e}")
