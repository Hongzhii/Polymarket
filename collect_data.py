from utils.websocket_utils import monitor_slugs
import asyncio
import yaml
import logging
import argparse

def main(slugs_and_dirs):
    async def run_monitors():
        tasks = [
            monitor_slugs(slugs, data_dir) for slugs, data_dir in slugs_and_dirs
        ]
        await asyncio.gather(*tasks)

    asyncio.run(run_monitors())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MarketMonitor.")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
        default="WARNING", 
        help="Set the logging level"
    )
    args = parser.parse_args()
    
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(message)s"
    )
    
    with open("datastreams.yaml") as f:
        config = yaml.safe_load(f)

    targets = [
        "Crypto",
    ]

    datastreams = config.get("datastreams", [])

    slugs_and_dirs = [
        (
            datastreams[target]["slugs"],
            datastreams[target]["directory"],
        )
        for target in targets
    ]

    main(slugs_and_dirs)