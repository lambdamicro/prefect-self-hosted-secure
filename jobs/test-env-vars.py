"""
Prefect flow to test retrieving and logging environment variables.
"""
import os
from prefect import flow, get_run_logger


@flow
async def start_test():
    """
    Prefect flow that retrieves the ENVIRONMENT environment variable and logs it.
    """
    logger = get_run_logger()
    logger.info("Starting environment variable test flow manage-buddy")
    
    environment = os.getenv("ENVIRONMENT")
    
    if environment:
        logger.info(f"ENVIRONMENT variable is set to: {environment}")
    else:
        logger.warning("ENVIRONMENT variable is not set")
    
    logger.info("Environment variable test flow completed")
    return environment


if __name__ == "__main__":
    import asyncio
    asyncio.run(start_test())
