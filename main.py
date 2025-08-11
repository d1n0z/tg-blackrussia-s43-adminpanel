import asyncio
import sys
import traceback

from loguru import logger

from db import dbhandle, Model

if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    logger.info("Starting...")

    logger.info("Creating tables...")
    dbhandle.create_tables(Model.__subclasses__())
    from Bot import Bot, sheets

    logger.info("Refilling sheets...")
    sheets.main(True, True, True)

    logger.info("Starting the bot...")
    try:
        asyncio.run(Bot().run())
    except KeyboardInterrupt:
        logger.info("Stopped by user (KeyboardInterrupt).")
    except Exception:
        logger.critical(traceback.format_exc())
