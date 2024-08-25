import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import pytest

from protoconfloader.protoconfloader import Configuration
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
    config = Configuration(message, "test_service", logging.getLogger())

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


if __name__ == "__main__":
    pytest.main()
