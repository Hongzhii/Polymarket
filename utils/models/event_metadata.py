from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass(frozen=True)
class MarketMetadata:
    id: str = field(
        metadata={
            "description": "Unique ID for identifying a market"
        }
    )

    cid: str = field(
        metadata={
            "description": "Unique ID for identifying a market"
        }
    )

    clobTID: Tuple[str, str] = field(
        metadata={
            "description": "Yes no options for the market, used for subscribing"
            "to market information"
        }
    )

    title: str

    slug: str = field(
        metadata={
            "description": "Unique plaintext title without whitespace"
        }
    )

    def __post_init__(self):
        if " " in self.slug:
            raise ValueError("No whitespace allowed in slug")

@dataclass(frozen=True)
class EventMetadata:
    id: str = field(
        metadata={
            "description": "Unique ID for identifying an event"
        }
    )

    title: str

    slug: str = field(
        metadata={
            "description": "Unique plaintext title without whitespace"
        }
    )

    markets: List[MarketMetadata]

    def __post_init__(self):
        if " " in self.slug:
            raise ValueError("No whitespace allowed in slug")
