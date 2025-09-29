from collections import defaultdict
from utils.gamma_utils import get_market_metadata
from typing import Dict, List
import asyncio
import time
import json
import logging
import os
import datetime
import websockets
import copy

class MarketMonitor:
    """
    Class instance that monitors markets handling asynchronus websocket
    connections and file writes.
    """
    def __init__(
        self,
        market_information: Dict,
        max_buffer_size: int = 1000,
        reconnect_delay: float = 5.0,
    ) -> None:
        self.market_group = market_information["market_group_name"]
        self.target_slugs = market_information["slugs"]
        if "directory" in market_information:
            self.output_dir = market_information["directory"]
        else:
            self.output_dir = os.path.join(
                "./data",
                self.market_group
            )

        self.url = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

        # Keep track of different monitoring sessions using UTC start time
        self.session_id = datetime.datetime.now(datetime.UTC).replace(
            microsecond=0
        )
        self.session_id = self.session_id.strftime('%Y-%m-%d %H:%M:%S')

        self.data_buffer = defaultdict(list)
        self.max_buffer_size = max_buffer_size
        self.cur_buffer_size = 0

        self.reconnect_delay = reconnect_delay
        self.cid_mapping = self._build()


    def _build(self):
        """
        Creates CID mappings and necessary data directories
        """
        def process_slug(slug):
            # Create the slug directory
            slug_dir = os.path.join(self.output_dir, slug)
            os.makedirs(
                slug_dir,
                exist_ok=True,
            )
            metadata = get_market_metadata(slug)

            process_market(slug_dir, metadata)

        def process_market(slug_dir, metadata):
            nonlocal cid_mapping
            # Create the individual market directoires
            for question, cids, outcomes in metadata:
                market_dir = os.path.join(slug_dir, question)
                os.makedirs(
                    market_dir,
                    exist_ok=True,
                )

                # Create the output files and populate mapping
                for cid, outcome in zip(cids, outcomes):
                    fp_outcome = os.path.join(
                        market_dir,
                        f"{outcome}_{self.session_id}",
                    ) + ".json"
                    cid_mapping[cid] = fp_outcome

        cid_mapping = {}
        for slug in self.target_slugs:
            process_slug(slug)

        return cid_mapping


    async def monitor(self):
        """
        This is the main event loop.
        """
        cids = list(self.cid_mapping.keys())

        last_time_pong = datetime.datetime.now()

        async with websockets.connect(self.url) as websocket:
            await websocket.send(
                json.dumps(
                    {
                        "assets_ids": cids,
                        "type": "market",
                    }
                )
            )
            try:
                while True:
                    m = await websocket.recv()
                    if m != "PONG":
                        last_time_pong = datetime.datetime.now()

                    updates = json.loads(m)
                    logging.info(f"Received: {updates}")

                    if isinstance(updates, dict):
                        updates = [updates]  # Wrap in a list for parsing

                    self.process_data(updates)

                    if (
                        last_time_pong + datetime.timedelta(seconds=10)
                        < datetime.datetime.now()
                    ):
                        await websocket.send("PING")

                    if self.cur_buffer_size > self.max_buffer_size:
                        self.flush_buffer()
            except KeyboardInterrupt:
                logging.info("Shutdown signal received.")
                self.flush_buffer()
                time.sleep(3) # To ensure buffer flush completes before exit
            except websockets.exceptions.ConnectionClosedError as e:
                logging.warning(
                    f"WebSocket connection closed: {e}. "
                    f"Reconnecting in {self.reconnect_delay} seconds..."
                )
                await asyncio.sleep(self.reconnect_delay)
            except Exception as e:
                logging.error(
                    f"Unexpected error: {e}. "
                    f"Reconnecting in {self.reconnect_delay} seconds..."
                )
                await asyncio.sleep(self.reconnect_delay)


    def flush_buffer(self):
        """
        Makes a deep copy of the buffer and writes it to file. Ensures that I/O
        does not block websocket monitoring.
        """
        buffer = copy.deepcopy(self.data_buffer)
        asyncio.create_task(
            asyncio.to_thread(
                self.write_buffer,
                buffer,
            )
        )
        
        # Reset buffer and count
        self.data_buffer = defaultdict(list)
        self.cur_buffer_size = 0


    def process_data(self, updates: List[Dict]):
        for update in updates:
            event_type = update["event_type"]
            match event_type:
                case "book":
                    cid = update["asset_id"]
                    self.data_buffer[cid].append(update)
                case "last_trade_price":
                    cid = update["asset_id"]
                    self.data_buffer[cid].append(update)
                case "price_change":
                    for change in update["price_changes"]:
                        cid = change["asset_id"]
                        self.data_buffer[cid].append(change)
                case _:
                    self.flush_buffer()
                    time.sleep(3) # Wait for buffer to flush
                    raise ValueError(
                        f"Unexpected event type encountered: {event_type}"
                    )
            self.cur_buffer_size += 1
        
    def write_buffer(self, buffer):
        timestamp = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f"Buffer write called at {timestamp}")

        for cid, updates in buffer.items():
            fp = self.cid_mapping[cid]

            with open(fp, "a") as f:
                for update in updates:
                    f.write(json.dumps(update) + "\n")
