import asyncio
import json
import logging
import os
import sys
from typing import Any, Callable

import aiofiles
import grpc
from google.protobuf.json_format import Parse
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from agent.api.proto.v1.protoconf_service_pb2 import ConfigSubscriptionRequest
from agent.api.proto.v1.protoconf_service_pb2_grpc import ProtoconfServiceStub

AGENTDEFAULTADDRESS = "localhost:4300"


class _EventHandler(FileSystemEventHandler):
    """
    A custom FileSystemEventHandler that watches for file modifications and triggers a callback function when the specified configuration file is modified.
    """

    def __init__(self, cb: Callable, config_file: str, logger: logging.Logger) -> None:
        """
        Initializes the event handler with a callback function and the name of the configuration file to watch.

        :param cb: The callback function to execute when the configuration file is modified.
        :param config_file: The name of the configuration file to watch for modifications.
        """
        self.config_file = config_file
        self.load_config_cb = cb
        self.logger = logger

    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handles file modification events. If the modified file is the configuration file specified during initialization, it runs the callback function.

        :param event: The FileSystemEvent object representing the file modification.
        """
        if os.path.basename(event.src_path) == self.config_file:
            try:
                asyncio.run(self.load_config_cb())
            except Exception:
                self.logger.error("Error loading config: %s", self.config_file)


class Configuration:
    """
    The `Configuration` class is designed to manage and monitor configuration
    files for changes.
    It loads configuration data from a specified file, watches for changes both
    locally and via a gRPC service,
    and updates the configuration accordingly. It also allows for a callback
    function to be executed whenever the configuration changes.
    """

    def __init__(self, message: Any, config_path: str, logger: logging.Logger) -> None:
        """
        Initializes the configuration with the given message and service name.
        """
        self.message = message
        self.logger = logger
        self.is_loaded = False
        self.is_watching_file = False
        self.is_watching_agent = False
        self.config_path = config_path
        self.config_file = None
        self.lock = asyncio.Lock()
        self.on_config_change_callback = None
        self.agent_address = AGENTDEFAULTADDRESS

    def set_logger(self, logger: logging.Logger) -> None:
        """
        Sets the logger for this configuration.
        """
        self.logger = logger

    async def load_config(self, config_path: str, config_name: str) -> None:
        """
        Loads the configuration from the specified file.
        """
        if self.is_loaded:
            return
        self.config_file = os.path.join(config_path, config_name)
        try:
            await self._load_config()
            self.is_loaded = True
        except FileNotFoundError as e:

            self.logger.error("Config file not found: %s", e)
            raise  # Re-raise the exception to allow the caller to handle it

    async def _load_config(self) -> None:
        """
        Internal method to load and parse the configuration file.
        """
        try:

            async with aiofiles.open(self.config_file, "r", encoding="utf-8") as f:
                config_data = json.loads(await f.read())
            async with self.lock:

                self.message = Parse(json.dumps(config_data), self.message)
            if self.on_config_change_callback is not None:
                await self.on_config_change_callback(self.message)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Error decoding JSON: {e}") from e

    def on_config_change(self, cb: Callable) -> None:
        """
        Sets a callback function to be called when the configuration changes.
        """
        self.on_config_change_callback = cb

    async def _listen_to_changes(self, path: str) -> None:
        """
        Listens for configuration updates via a gRPC service.
        """
        # path = "crawler/text_crawler"
        self.logger.info("Listening to changes for %s", path)  # Use lazy % formatting
        try:
            async with grpc.aio.insecure_channel(self.agent_address) as channel:
                client = ProtoconfServiceStub(channel)
                request = ConfigSubscriptionRequest(path=path)
                async for config_update in client.SubscribeForConfig(request):
                    async with self.lock:
                        config_update.value.Unpack(self.message)
                    if self.on_config_change_callback is not None:
                        await self.on_config_change_callback(self.message)
        except grpc.RpcError as e:
            self.logger.error(
                "Error with gRPC communication: %s", e
            )  # Use lazy % formatting
            raise  # Re-raise the exception to allow the caller to handle it

    async def _file_watcher(self, delay: int = 0) -> None:
        """
        Watches the configuration file for changes and reloads it if modified.
        """
        self.logger.info("Starting watching config file")
        handler = _EventHandler(self._load_config, self.config_file, self.logger)
        observer = Observer()
        observer.schedule(handler, self.config_file, recursive=True)
        observer.start()
        self.logger.info("Observer started")
        try:
            while True:
                await asyncio.sleep(delay)
        finally:
            observer.stop()
            observer.join()

    async def watch_config(self, delay: int = 0) -> None:
        """
        Starts both the file watcher and gRPC listener tasks with exception handling.
        """
        try:
            async with asyncio.TaskGroup() as tg:
                task1 = tg.create_task(self._listen_to_changes(self.config_path))
                task2 = tg.create_task(self._file_watcher(delay))
        except asyncio.CancelledError:
            self.logger.info("Tasks were cancelled")
        except Exception as e:
            self.logger.error("Error in watch_config: %s", e)
            # Removed the incorrect handling of exceptions as instances of Exception do not have an 'exceptions' member
            # Instead, directly log the exception and its traceback
            self.logger.error("Error traceback: ", exc_info=e)
            sys.exit(os.EX_UNAVAILABLE)
