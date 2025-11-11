from enum import Enum

URL_REST = "https://gamma-api.polymarket.com"
URL_WS = "wss://ws-subscriptions-clob.polymarket.com/ws"
URL_DATA = "https://data-api.polymarket.com/"
URL_RTDS = "wss://ws-live-data.polymarket.com"

class Frequencies(Enum):
    YEARLY = "Yearly"
    MONTHLY = "Monthly"
    DAILY = "Daily"

class Currencies(Enum):
    BITCOIN = "Bitcoin"
    ETHEREUM = "Ethereum"