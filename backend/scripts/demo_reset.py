from __future__ import annotations

import asyncio
import logging
import os

try:
    from scripts import seed
except ModuleNotFoundError:
    import seed

logger = logging.getLogger("snail.demo_reset")


def ensure_not_prod() -> None:
    if os.environ.get("ENV", "local").lower() == "prod":
        logger.error("demo_reset refused because ENV=prod")
        raise SystemExit(1)


async def async_main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    ensure_not_prod()
    await seed.seed_database(reset=True)
    logger.info("demo_reset.completed")


if __name__ == "__main__":
    asyncio.run(async_main())
