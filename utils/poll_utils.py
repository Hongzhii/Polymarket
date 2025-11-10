import httpx
import asyncio
import requests
import json
from enum import Enum

URL = "https://gamma-api.polymarket.com"

class Frequencies(Enum):
    YEARLY = "Yearly"
    MONTHLY = "Monthly"
    DAILY = "Daily"

class Currencies(Enum):
    BITCOIN = "Bitcoin"
    ETHEREUM = "Ethereum"

def load_tag_info(fp):
    with open(fp) as f:
        tmp = json.load(f)

        tag_info = {}

        for tag in tmp:
            try:
                tag_info[tag["label"]] = tag
            except KeyError:
                pass

    return tag_info


def get_pages(
    url,
    results_per_page,
    params,
    verbose=False,
):
    with requests.Session() as session:
        params["limit"] = results_per_page
        cur_offset = 0

        results = []

        while True:
            if verbose:
                print(f"Processing page: {cur_offset+1}")
            params["offset"] = cur_offset * results_per_page

            response = session.get(
                url=url,
                params=params,
            ).json()

            if verbose:
                print(len(response))

            if len(response) == 0:
                break

            results += response
            cur_offset += 1

        return results


def search_by_tag(
    url: str,
    tag_id: int,
    results_per_page: int = 200,
):
    params = {
        "closed": False,
        "tag_id": tag_id,
    }
    results = get_pages(
        url=url,
        results_per_page=results_per_page,
        params=params,
    )

    return results

async def get_crypto_option_event(
    tag_info,
    freq: Frequencies,
    currency: Currencies
):
    tags = ["Crypto", "Crypto Prices", "Hit Price"]
    tags.append(freq.value)
    tags.append(currency.value)

    ids = [tag_info[tag]["id"] for tag in tags]

    tag_fetch_tasks = []

    for id in ids:
        tag_fetch_tasks.append(
            asyncio.to_thread(
                search_by_tag,
                url=f"{URL}/events",
                tag_id=id,
            )
        )
    results = await asyncio.gather(*tag_fetch_tasks)

    result_ids = []
    for result in results:
        ids = {
            response["id"] for response in result
        }
        result_ids.append(ids)

    common_ids = set.intersection(*result_ids)

    return common_ids


async def poll_events():
    tag_info = load_tag_info("tag_info.json")

    tasks = []
    keys = []

    for f in Frequencies:
        for c in Currencies:
            tasks.append(
                get_crypto_option_event(
                    tag_info=tag_info,
                    freq=f,
                    currency=c,
                )
            )
            keys.append((f.value, c.value))

    results = await asyncio.gather(*tasks)

    mapped = {keys[i]: sorted(list(results[i])) for i in range(len(results))}


if __name__=="__main__":
    asyncio.run(poll_events())