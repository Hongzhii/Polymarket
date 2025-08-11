"""
Websockets utility functions for asynchronous communication.

This module handles communication with the PolyMarket API for collection of
market book data and saves collected data to file.
"""

import json
import datetime
import os
import logging
import asyncio
from typing import List
import websockets

from utils.gamma_utils import get_market_metadata
from utils.utils import get_asset_id_mapping, simplify_mapping_dict


async def monitor_market(asset_ids, output_fp, title=None):
    """
    Monitors market data for specified asset IDs via a websocket connection and
    saves updates to a JSON file. Connects to the Polymarket websocket API,
    subscribes to updates for the given asset IDs, and continuously receives
    market data. The received data is appended to the specified output file in
    JSON format. Optionally, a title can be printed to indicate which market is
    being monitored. The function also manages websocket keep-alive by sending
    "PING" messages if no "PONG" is received within a set interval.

    Args:
        asset_ids (list): List of asset IDs to monitor.
        output_fp (str): File path (without extension) where the output JSON
            data will be saved.
        title (str, optional): Optional title to display when monitoring
            starts.
    Returns:
        None
    """
    url = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    last_time_pong = datetime.datetime.now()

    if title:
        print(f"Monitoring: {title}")

    async with websockets.connect(url) as websocket:
        await websocket.send(
            json.dumps({"assets_ids": asset_ids, "type": "market"})
        )

        while True:
            exists = os.path.exists(output_fp)

            m = await websocket.recv()
            if m != "PONG":
                last_time_pong = datetime.datetime.now()
            d = json.loads(m)

            if isinstance(d, dict):
                d = [d]  # Wrap in a list for parsing
            print(d)

            d = [str(_) if str(_).startswith('"') else f'"{str(_)}"' for _ in d]

            if exists:
                with open(output_fp, "r+") as f:
                    f.seek(0, 2)  # Seek to the end
                    f.seek(f.tell() - 1)  # One char from end
                    f.write(f",{','.join(d)}]")
            else:
                with open(output_fp, "w") as f:
                    json.dump(d, f)
            if (
                last_time_pong + datetime.timedelta(seconds=10)
                < datetime.datetime.now()
            ):
                await websocket.send("PING")


async def monitor_by_slug(slug: str, data_dir: str) -> None:
    """
    Monitors a market by its slug and manages asset ID mappings.
    Loads asset ID mappings from a cache file if available; otherwise, fetches
    market metadata and generates new mappings. The mappings are then saved to
    the cache file. Finally, the function monitors the market using the asset
    IDs and saves the output to a JSON file.

    Args:
        slug (str): The market slug used to identify the market.
        data_dir (str): The directory path where mapping and output files are
            stored.
    Returns:
        None
    """
    fp_mappings = os.path.join(data_dir, "mappings.json")
    mappings = None

    if os.path.exists(fp_mappings):
        try:
            with open(fp_mappings, "r") as f:
                mappings = json.load(f)
        except json.decoder.JSONDecodeError:
            logging.info("Error with JSON formatting.")
            logging.info("Querying Polymarket API for asset IDs...")

    if not mappings:  # Get mappings from Polymarket API
        metadata = get_market_metadata(slug)
        mappings = get_asset_id_mapping(metadata)
        mappings = simplify_mapping_dict(mappings)

        with open(os.path.join(data_dir, "mappings.json"), "w") as f:
            # Process mappings
            json.dump(mappings, f)

    await monitor_market(
        asset_ids=list(mappings.keys()),
        output_fp=os.path.join(data_dir, "market_data.json"),
    )


async def monitor_slugs(slugs: List[str], market_data_dir: str) -> None:
    """
    Monitors multiple market slugs asynchronously and saves their data.
    For each slug in the provided list, this function creates an asynchronous
    monitoring task and executes all tasks concurrently. The monitoring logic
    for each slug is handled by the `monitor_by_slug` function.

    Args:
        slugs (List[str]): A list of market slugs to monitor.
        data_dir (str): The directory path where monitored data should be saved.
    Returns:
        None
    """
    tasks = []

    for slug in slugs:
        data_dir = os.path.join(market_data_dir, slug)
        os.makedirs(data_dir, exist_ok=True)

        task = asyncio.create_task(monitor_by_slug(slug, data_dir))
        tasks.append(task)

    await asyncio.gather(*tasks)
