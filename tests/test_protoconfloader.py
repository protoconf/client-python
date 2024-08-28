import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import pytest
from watchdog.events import FileSystemEvent
from protoconfloader.protoconfloader import Configuration, _EventHandler
from tests.test_data.crawler_pb2 import CrawlerService


@pytest.mark.asyncio
async def test_load_config_local():
    # Setup
    mock_open = AsyncMock()
    mock_open.return_value.__aenter__.return_value.read = AsyncMock(
        return_value='{"crawlers": []}'
    )
    message = CrawlerService()
    config = Configuration(message, "test_service", logging.getLogger())

    # Act
    await config.load_config("tests/test_data", "config.json")

    assert message.log_level == 3


@pytest.mark.asyncio
async def test_load_invalid_json_config():
    # Setup
    mock_open = AsyncMock()
    mock_open.return_value.__aenter__.return_value.read = AsyncMock(
        return_value='{"crawlers": [}'  # Invalid JSON
    )
    message = CrawlerService()
    config = Configuration(message, "crawler/text_crawler", logging.getLogger())

    # Act & Assert
    with patch("builtins.open", mock_open):
        with pytest.raises(RuntimeError, match="Error decoding JSON"):
            await config.load_config("tests/test_data", "invalid_config.json")


@pytest.mark.asyncio
async def test_listen_to_changes_remote():
    # Setup
    mock_channel = AsyncMock()
    mock_client = MagicMock()
    mock_client.SubscribeForConfig = AsyncMock(
        return_value=iter([MagicMock(value=MagicMock())])
    )
    mock_channel.return_value.__aenter__.return_value = mock_client
    message = CrawlerService()
    config = Configuration(message, "crawler/text_crawler", logging.getLogger())
    mock_callback = AsyncMock()
    callback_event = asyncio.Event()

    # Act
    await config.load_config("tests/test_data", "config.json")

    async def async_callback(message):
        await mock_callback(message)
        callback_event.set()

    config.on_config_change(async_callback)
    watch_task = asyncio.create_task(config.watch_config())

    await asyncio.sleep(0.3)

    # Assert
    assert callback_event.is_set()
    mock_callback.assert_called_once()
    watch_task.cancel()
    await asyncio.gather(watch_task, return_exceptions=True)


@pytest.mark.asyncio
async def test_load_config_nonexistent_file():
    # Setup
    message = CrawlerService()
    config = Configuration(message, "test_service", logging.getLogger())
    mock_callback = AsyncMock()
    callback_event = asyncio.Event()

    # Act
    async def async_callback(message):
        await mock_callback(message)
        callback_event.set()

    config.on_config_change(async_callback)

    # Act & Assert
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            await config.load_config("tests/test_data", "nonexistent_config.json")

        assert not callback_event.is_set()
        mock_callback.assert_not_called()


@pytest.mark.asyncio
async def test_watch_config_remote_same_log_level():
    # Setup
    mock_channel = AsyncMock()
    mock_client = MagicMock()
    mock_client.SubscribeForConfig = AsyncMock(
        return_value=iter([MagicMock(value=MagicMock(log_level=3))])
    )
    mock_channel.return_value.__aenter__.return_value = mock_client
    message = CrawlerService()
    config = Configuration(message, "crawler/text_crawler", logging.getLogger())
    mock_callback = AsyncMock()
    callback_event = asyncio.Event()

    # Act
    await config.load_config("tests/test_data", "config.json")

    async def async_callback(message):
        await mock_callback(message)
        callback_event.set()

    config.on_config_change(async_callback)
    watch_task = asyncio.create_task(config.watch_config())

    await asyncio.sleep(0.3)

    # Assert
    assert callback_event.is_set()
    mock_callback.assert_called_once()
    assert message.log_level == 17
    watch_task.cancel()
    await asyncio.gather(watch_task, return_exceptions=True)


def test_on_modified_nonexistent_file():
    # Setup
    event = FileSystemEvent("nonexistent_config.json")
    mock_logger = MagicMock()
    handler = _EventHandler(
        cb=MagicMock(), config_file="nonexistent_config.json", logger=mock_logger
    )

    # Act
    handler.on_modified(event)

    # Assert
    # handler.load_config_cb.assert_not_called()

    mock_logger.error.assert_called_once_with(
        "Error loading config: %s", "nonexistent_config.json"
    )


def test_set_logger():
    # Setup
    config = Configuration(
        message=Mock(), config_path="crawler/text_crawler", logger=logging.getLogger()
    )
    new_logger = logging.getLogger("new_logger")

    # Act
    config.set_logger(new_logger)

    # Assert
    assert config.logger == new_logger


if __name__ == "__main__":
    pytest.main()
