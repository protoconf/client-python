import asyncio
import logging

from tests.test_data.crawler_pb2 import CrawlerService
from google.protobuf.struct_pb2 import Struct


from protoconfloader.protoconfloader import Configuration


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Struct message to hold our configuration
config_message = CrawlerService()

# Initialize the Configuration object
config = Configuration(
    config_message,
    "crawler/text_crawler",
    logger,
)


# Callback function to handle configuration changes
async def on_config_change(new_config):
    """
    This function is a callback for configuration changes.
    It logs the changes in the configuration.
    """
    logger.info(
        "DemoApp Configuration changed:: New Log Level %s", new_config.log_level
    )


async def main():
    """
    This is the main function of the application.
    It sets up the configuration, loads the initial configuration, watches for configuration changes,
    and simulates a long-running process.
    """
    # Set the callback function
    config.on_config_change(on_config_change)

    # Load the initial configuration
    await config.load_config(".", "config.json")

    # Start watching for configuration changes
    watch_task = asyncio.create_task(config.watch_config())

    # Run the app for a while (simulating a long-running process)
    try:
        await asyncio.sleep(300)  # Run for 5 minutes
    except asyncio.CancelledError:
        logger.info("App is shutting down")
    finally:
        watch_task.cancel()
        await asyncio.gather(watch_task, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
