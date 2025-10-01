from utils.websocket_utils import monitor_slugs
import asyncio
import os
import yaml

def main(slugs_and_dirs):
    async def run_monitors():
        tasks = [
            monitor_slugs(slugs, data_dir) for slugs, data_dir in slugs_and_dirs
        ]
        await asyncio.gather(*tasks)

    asyncio.run(run_monitors())


if __name__ == "__main__":
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