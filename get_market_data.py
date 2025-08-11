from utils.websocket_utils import monitor_slugs
import asyncio


def main(slugs, data_dir):
    asyncio.run(
        monitor_slugs(
            slugs,
            data_dir,
        )
    )


if __name__ == "__main__":
    # Example slugs to monitor
    SLUGS = [
        "democratic-presidential-nominee-2028",
        "republican-presidential-nominee-2028",
        "presidential-election-winner-2028",
        "which-party-wins-2028-us-presidential-election",
    ]
    DATA_DIR = "./data/market_data"

    main(SLUGS, DATA_DIR)
