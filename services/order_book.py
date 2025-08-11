from typing import Mapping, Optional
import logging
import os
import datetime

from utils.utils import unix_to_utc, load_data_cache


class OrderBook:
    """
    A class to represent the order book for a given asset.

    Attributes:
        order_books (dict): A dictionary of order books, keyed by asset ID.
        asset_id_mapping (dict): A dictionary mapping asset IDs to their descriptions.
    """

    def __init__(
        self,
        asset_id_mapping: Mapping,
        fp_data: str,
        target_market: Optional[str] = None,
    ) -> None:
        self.order_books = {}
        self.asset_id_mapping = asset_id_mapping
        self.fp_data = fp_data
        self.data = load_data_cache(self.fp_data)
        self.history = list()

        if target_market:
            self.data = [
                data for data in self.data if data["asset_id"] == target_market
            ]

        self.data = iter(self.data)

    def _update_price(
        self,
        update: Mapping,
    ) -> None:
        """
        Updates the price in the order book based on the provided update.

        Args:
            update (Mapping): A dictionary containing the price update information.
        """
        target_book = self.order_books[update["asset_id"]]

        for change in update["changes"]:
            price, side, size = change["price"], change["side"], change["size"]

            target = "bids" if side == "BUY" else "asks"
            counter_target = "asks" if side == "BUY" else "bids"

            updated = False

            for i, price_dict in enumerate(target_book[target]):
                if price_dict["price"] == price and size == "0":
                    target_book[target].pop(i)
                    updated = True
                    break
                elif price_dict["price"] == price:
                    price_dict["size"] = str(size)
                    updated = True
                    break

            for i, price_dict in enumerate(target_book[counter_target]):
                if price_dict["price"] == price:
                    size_diff = round(
                        float(price_dict["size"]) - float(size), 3
                    )

                    if size_diff == 0:
                        target_book[counter_target].pop(i)
                    elif size_diff > 0:
                        price_dict["size"] = size_diff
                    else:
                        target_book[target].append(
                            {
                                "price": price,
                                "size": str(-size_diff),
                            }
                        )

                    updated = True
                    break

            if updated:
                continue

            target_book[target].append(
                {
                    "price": price,
                    "size": size,
                }
            )

        target_book["bids"] = sorted(
            target_book["bids"], key=lambda x: float(x["price"])
        )
        target_book["asks"] = sorted(
            target_book["asks"], key=lambda x: float(x["price"])
        )

    def _update_book(
        self,
        update: Mapping,
    ) -> None:
        """
        Updates the order book with the provided update.

        Args:
            update (Mapping): A dictionary containing the order book update information.
        """
        if update["asset_id"] not in self.order_books:
            logging.info(
                f"Creating new order book for {self.asset_id_mapping[update['asset_id']]}"
            )

        update["bids"] = sorted(update["bids"], key=lambda x: float(x["price"]))
        update["asks"] = sorted(update["asks"], key=lambda x: float(x["price"]))
        self.order_books[update["asset_id"]] = update

    def update(
        self,
        update: Mapping,
    ) -> None:
        """
        Updates the order book based on the event type in the provided update.

        Args:
            update (Mapping): A dictionary containing the update information.
        """

        match update["event_type"]:
            case "price_change":
                self._update_price(update)
            case "book":
                self._update_book(update)
            case "tick_size_change":
                pass
            case "last_trade_price":
                pass
            case _:
                # Handle unknown event type
                logging.warning(f"Unknown event type: {update['event_type']}")

    def display_book(
        self,
        asset_id: str,
    ) -> None:
        """
        Displays the order book for the given asset ID.

        Args:
            asset_id (str): The ID of the asset to display the order book for.
        """
        if asset_id not in self.asset_id_mapping:
            logging.warning(f"Id not found: {asset_id}")
            return

        book = self.order_books[asset_id]

        bids = book["bids"]
        asks = book["asks"]

        print(f"==={self.asset_id_mapping[asset_id]}===")

        print("TYPE\tPRICE\tSIZE")

        if len(asks) != 0:
            for ask in asks[::-1]:
                price, size = ask["price"], ask["size"]
                print(f"ASK\t{price}\t{size}")

        if len(asks) != 0 and len(bids) != 0:
            spread = float(asks[0]["price"]) - float(bids[-1]["price"])
            price = (float(asks[0]["price"]) + float(bids[-1]["price"])) / 2.0
            print(f"-----SPREAD: {spread:.3f}  PRICE: {price:.3f}-----")
        else:
            print("-----SPREAD: INVALID  PRICE: INVALID-----")

        if len(bids) != 0:
            for bid in bids[::-1]:
                price, size = bid["price"], bid["size"]
                print(f"BID\t{price}\t{size}")

    def next_tick(
        self,
    ) -> datetime.datetime:
        """
        Advances the order book to the next tick of data.

        This method clears the console, retrieves the next update from the
        data stream, prints the UTC timestamp of the update, applies the
        update to the order book, and displays the updated order book for
        the relevant asset.

        Returns:
            timestamp (datetime.datetime): Datetime of the current update
        """
        os.system("cls" if os.name == "nt" else "clear")

        next_update = next(self.data)

        timestamp = unix_to_utc(next_update["timestamp"])

        print(f"UTC: {timestamp}")

        asset_id = next_update["asset_id"]

        self.update(next_update)
        self.display_book(asset_id)

        return timestamp

    def reset(
        self,
        timestamp: Optional[datetime.datetime] = None,
    ) -> None:
        """
        Resets the internal data iterator.

        Args:
            timestamp (Optional[datetime.datetime], optional): If provided,
                the data iterator will be reset to start from this timestamp.
                If None, the iterator will start from the beginning of the
                data file. Defaults to None.

        Returns:
            None
        """
        if timestamp:
            self.data = iter(load_data_cache(self.fp_data, timestamp=timestamp))
        else:
            self.data = iter(load_data_cache(self.fp_data))
