from dataclasses import dataclass, field, Field
from typing import Annotated, List, Tuple
from utils.constants import Side

def TimestampField() -> Field:
    return field(
        metadata={
            "description": "Unix timestamp of update time in milliseconds"
        }
    )

def TokenIdField() -> Field:
    return field(
        metadata={
            "description": "Unique ID identifying a CLOB market. Which " \
                "corresponds to the market book containing the bid and ask " \
                "prices of a particular market outcome"
        }
    )

@dataclass(frozen=True)
class OrderSummary:
    price: float
    size: float

@dataclass(frozen=True)
class BookUpdate:
    buys: List[OrderSummary]
    sells: List[OrderSummary]
    timestamp: Annotated[int, TimestampField()]

@dataclass(frozen=True)
class PriceChange:
    price: float
    size: float
    side: Side
    clob_tid: Annotated[str, TokenIdField()]

@dataclass(frozen=True)
class PriceChangeUpdate:
    price_changes: List[PriceChange]
    timestamp: Annotated[int, TimestampField()]

@dataclass(frozen=True)
class TickSizeChangeUpdate:
    old_tick_size: float
    new_tick_size: float
    side: Side
    clob_tid: Annotated[str, TokenIdField()]
    timestamp: Annotated[int, TimestampField()]

@dataclass(frozen=True)
class LastTradePriceUpdate:
    price: float
    size: float
    side: Side
    clob_tid: Annotated[str, TokenIdField()]
    timestamp: Annotated[int, TimestampField()]