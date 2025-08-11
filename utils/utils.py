"""
General utility functions
"""

import datetime
import ast
import logging

from typing import Mapping, List, Optional


def get_asset_id_mapping(market_metadata):
    data_dict = dict()

    for market in market_metadata:
        question, clob_tid, outcomes = market

        data_dict[clob_tid[0]] = question + " " + outcomes[0]
        data_dict[clob_tid[1]] = question + " " + outcomes[1]

    return data_dict


def simplify_mapping_dict(
    mapping: Mapping,
) -> Mapping:
    """
    Processes mapping dictionaries and shortens key lengths.

    Args:
        fp_mapping (str): File path to the mapping JSON file.

    Returns:
        None
    """
    name_format_conversion = {
        "J.D. Vance": "JD Vance",
        "Stephen A. Smith": "Stephen Smith",
        "J.B. Pritzker": "JB Pritzker",
    }

    new_mappings = {}

    for asset_id, question in mapping.items():
        # Extract outcome (Yes/No)
        outcome = (
            "Yes"
            if question.strip().endswith("Yes")
            else "No" if question.strip().endswith("No") else None
        )

        # Extract person name
        # Remove "Will ", outcome, and everything after "win the"
        q = question.strip()
        if " win the " in q:
            person = q.split(" win the ")[0].replace("Will ", "").strip()
        elif " win " in q:
            person = q.split(" win ")[0].replace("Will ", "").strip()
        else:
            person = None

        if person:
            if person in name_format_conversion:
                person = name_format_conversion[person]
            new_mappings[asset_id] = f"{person} | {outcome}"
        else:
            logging.info("Unknown data format, mapping dict processing skipped")
            return mapping

    return new_mappings


def load_data_cache(
    fp: str,
    timestamp: Optional[datetime.datetime] = None,
) -> List[Mapping]:
    """
    Loads cached market data from a file.

    If a timestamp is provided, the function filters the data to include
    only entries with timestamps greater than or equal to the provided
    timestamp.

    Args:
        fp (str): The file path to the cached data.
        timestamp (datetime.datetime, optional): The datetime object to
            filter the data from. Defaults to None.

    Returns:
        List[Mapping]: A list of parsed data entries, or an empty list if loading fails.
    """
    result = []
    try:
        with open(fp) as f:
            raw_data = ast.literal_eval(f.read())
            for data in raw_data:
                try:
                    data = ast.literal_eval(data)

                    if isinstance(data, str):
                        data = ast.literal_eval(data)

                    result.append(data)
                except (ValueError, SyntaxError) as e:
                    print(f"Error parsing entry: {e}")
    except (FileNotFoundError, IOError) as e:
        print(f"Error opening file: {e}")
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing file contents: {e}")

    if timestamp:
        for i, entry in enumerate(result):
            if unix_to_utc(entry["timestamp"]) > timestamp:
                threshold_index = i
                break
        result = result[threshold_index:]

    return result


def unix_to_utc(timestamp: str) -> datetime.datetime:
    """
    Converts a Unix timestamp (in milliseconds) to a UTC datetime object.

    Args:
        timestamp (str): A Unix timestamp in milliseconds.

    Returns:
        datetime.datetime: A datetime object representing the timestamp in UTC.
    """
    if len(timestamp) == 13:
        timestamp = timestamp[:-3]

    return datetime.datetime.fromtimestamp(
        int(timestamp),
        datetime.UTC,
    )
