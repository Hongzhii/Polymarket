from services.market_book import MarketBook
from services.exceptions import NoValidStatesError
import json
import os
import time
import logging
from typing import Dict, Tuple, Optional, List
import sys
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout


def load_mapping(fp):
    with open(fp) as f:
        data = json.load(f)

    return {v: k for k, v in data.items()}


def get_best_bid_ask(
    aid: int, fp_data: str, index: Optional[int] = -1
) -> Tuple[int, int]:
    """
    Retrieves the best bid and ask prices for a given outcome from the market book.

    Args:
        aid (int): The identifier for the asset or outcome.
        fp_data (str): The market book data in string format.
        index (Optional[int], optional): The index of the price to retrieve.
            Defaults to -1, which returns the most recent prices.
    Returns:
        Tuple[int, int]: A tuple containing the best bid price and the best ask price.
    """
    book = MarketBook(
        aid,
        fp_data,
    )
    bid, _ = book.get_best_bid(index)
    ask, _ = book.get_best_ask(index)

    return bid, ask


def party_arb_margin(
    dem_candidates: List[str],
    gop_candidates: List[str],
    pres_data_dir: str,
    party_data_dir: str,
) -> Dict[str, float]:
    def get_ask_prices(name, data_dir, mapping=None):
        """
        Returns the current yes and no market ask prices for the candidate.
        """
        if not mapping:
            mapping = load_mapping(os.path.join(data_dir, "mappings.json"))

        yes_outcome = f"{name} | Yes"
        no_outcome = f"{name} | No"

        aid_yes = mapping[yes_outcome]
        aid_no = mapping[no_outcome]

        book_yes = MarketBook(
            aid_yes, os.path.join(data_dir, "market_data.json")
        )
        yes_ask = book_yes.get_best_ask(-1)[0]

        book_no = MarketBook(aid_no, os.path.join(data_dir, "market_data.json"))
        no_ask = book_no.get_best_ask(-1)[0]

        return round(yes_ask, 3), round(no_ask, 3)

    candidate_mapping = load_mapping(
        os.path.join(pres_data_dir, "mappings.json")
    )

    synth_dem_yes = 0
    synth_dem_no = 0
    synth_gop_yes = 0
    synth_gop_no = 0

    num_dems = 0
    num_gops = 0

    for dem_candidate, gop_candidate in zip(dem_candidates, gop_candidates):
        try:
            dem_can_yes, dem_can_no = get_ask_prices(
                dem_candidate, pres_data_dir, candidate_mapping
            )
            synth_dem_yes += dem_can_yes
            synth_dem_no += dem_can_no
            num_dems += 1
        except NoValidStatesError as e:
            logging.info(
                f"{dem_candidate} has no valid states in Presidential candidates market"
            )

        try:
            gop_can_yes, gop_can_no = get_ask_prices(
                gop_candidate, pres_data_dir, candidate_mapping
            )
            synth_gop_yes += gop_can_yes
            synth_gop_no += gop_can_no
            num_gops += 1
        except NoValidStatesError as e:
            logging.info(
                f"{gop_candidate} has no valid states in Presidential candidates market"
            )

    # Normalize for the fact that only one candidate from a party can win
    synth_dem_no -= num_dems - 1
    synth_gop_no -= num_gops - 1

    party_mapping = load_mapping(os.path.join(party_data_dir, "mappings.json"))
    dem_yes, dem_no = get_ask_prices(
        "the Democrats", party_data_dir, party_mapping
    )
    gop_yes, gop_no = get_ask_prices(
        "the Republicans", party_data_dir, party_mapping
    )

    synth_dem_yes = round(synth_dem_yes, 3)
    synth_dem_no = round(synth_dem_no, 3)
    synth_gop_yes = round(synth_gop_yes, 3)
    synth_gop_no = round(synth_gop_no, 3)

    # Cross party arbs assume that only one of the two parties can win
    cross_party_positive_arb = round(1 - (synth_dem_yes + gop_yes), 3)
    cross_party_negative_arb = round(1 - (synth_dem_no + gop_no), 3)

    # Intra party arbs are 100% safe
    intra_dem_arb_1 = round(1 - (synth_dem_yes + dem_no), 3)
    intra_dem_party_arb_2 = round(1 - (synth_dem_no + dem_yes), 3)
    intra_gop_arb_1 = round(1 - (synth_gop_yes + gop_no), 3)
    intra_gop_party_arb_2 = round(1 - (synth_gop_no + gop_yes), 3)

    return {
        "synth_dem_yes": synth_dem_yes,
        "synth_dem_no": synth_dem_no,
        "synth_gop_yes": synth_gop_yes,
        "synth_gop_no": synth_gop_no,
        "dem_yes": dem_yes,
        "dem_no": dem_no,
        "gop_yes": gop_yes,
        "gop_no": gop_no,
        "intra_dem_arb_1": intra_dem_arb_1,
        "intra_dem_party_arb_2": intra_dem_party_arb_2,
        "intra_gop_arb_1": intra_gop_arb_1,
        "intra_gop_party_arb_2": intra_gop_party_arb_2,
        "cross_party_positive_arb": cross_party_positive_arb,
        "cross_party_negative_arb": cross_party_negative_arb,
    }


def calculate_conditional_odds(aid_yes_pres, aid_yes_party, fp_pres, fp_party):
    try:
        yes_pres_bid, yes_pres_ask = get_best_bid_ask(aid_yes_pres, fp_pres)
        yes_party_bid, yes_party_ask = get_best_bid_ask(aid_yes_party, fp_party)

        yes_pres_price = (yes_pres_bid + yes_pres_ask) / 2
        yes_party_price = (yes_party_bid + yes_party_ask) / 2

        return round(yes_pres_price / yes_party_price, 4)
    except NoValidStatesError:
        print(f"No valid states for pres_id={aid_yes_pres}, party_id={aid_yes_party}")


def get_conditional_odds(
    candidates,
    pres_dir,
    candidate_party_dir,
    mapping_pres=None,
    mapping_party_candidate=None,
):
    if not mapping_pres:
        mapping_pres = load_mapping(os.path.join(pres_dir, "mappings.json"))
    if not mapping_party_candidate:
        mapping_party_candidate = load_mapping(
            os.path.join(candidate_party_dir, "mappings.json")
        )

    result = {}

    for candidate in candidates:
        try:
            aid_yes_pres = mapping_pres[f"{candidate} | Yes"]
            aid_yes_party = mapping_party_candidate[f"{candidate} | Yes"]
        except KeyError:
            logging.info(f"{candidate} does not have valid mapping")
            continue

        fp_market_data_pres = os.path.join(pres_dir, "market_data.json")
        fp_market_data_party = os.path.join(candidate_party_dir, "market_data.json")

        conditional_odds = calculate_conditional_odds(
            aid_yes_pres,
            aid_yes_party,
            fp_market_data_pres,
            fp_market_data_party,
        )

        result[candidate] = conditional_odds

    result = dict(sorted(result.items(), key=lambda item: item[1] if item[1] is not None else float('-inf'), reverse=True))

    return result


def render_dashboard(
    probabilities, gop_conditional_odds, dem_condidtional_odds
):
    layout = Layout()

    # Party Arbitrage Table
    party_table = Table(
        title="Party Arbitrage Margins",
        caption=(
            "Pseudo party win probabilities are calculated by summing the prices of all candidates representing a party in the presidential election winner market. "
            "This sum serves as a proxy for the probability that the party wins the election. "
            "For the 'No' prices, we sum all the 'No' prices for each candidate and subtract (n-1), where n is the number of candidates for that party, to obtain the proxy 'No' value. "
            "Price differences between these proxies and the actual party market prices can be exploited for arbitrage opportunities."
        ),
        expand=True
    )
    party_table.add_column("Metric", style="bold")
    party_table.add_column("Value", style="cyan")

    highlight_keys = {
        "intra_dem_arb_1",
        "intra_dem_party_arb_2",
        "intra_gop_arb_1",
        "intra_gop_party_arb_2",
        "cross_party_positive_arb",
        "cross_party_negative_arb",
    }

    for k, v in probabilities.items():
        value_str = str(v)
        if isinstance(v, (int, float)):
            if v < 0:
                value_style = "red"
            elif v > 0.2:
                value_style = "blue"
            else:
                value_style = "green"
        else:
            value_style = "cyan"

        if k in highlight_keys:
            metric_style = "bold yellow"
        else:
            metric_style = "bold"

        party_table.add_row(f"[{metric_style}]{k}[/{metric_style}]", f"[{value_style}]{value_str}[/{value_style}]")

    # GOP Conditional Odds Table
    gop_table = Table(
        title="GOP Conditional Odds",
        caption=(
            "Conditional odds represent the market-implied probability that a candidate will win the presidency "
            "given they are nominated by their party. This is calculated as:\n"
            "P(Candidate wins presidency) / P(Candidate is nominated)\n"
            "Assumes candidates only run under their party and not as independents. "
            "Conditional odds > 1 may occur if the market expects a candidate to run as an independent while also having a strong chance of winning."
        ),
        expand=True
    )
    gop_table.add_column("Candidate", style="bold")
    gop_table.add_column("Odds", style="magenta")
    for k, v in gop_conditional_odds.items():
        gop_table.add_row(k, str(v) if v is not None else "-")

    # DEM Conditional Odds Table
    dem_table = Table(
        title="DEM Conditional Odds",
        caption=(
            "Conditional odds represent the market-implied probability that a candidate will win the presidency "
            "given they are nominated by their party. This is calculated as:\n"
            "P(Candidate wins presidency) / P(Candidate is nominated)\n"
            "Assumes candidates only run under their party and not as independents. "
            "Conditional odds > 1 may occur if the market expects a candidate to run as an independent while also having a strong chance of winning."
        ),
        expand=True
    )
    dem_table.add_column("Candidate", style="bold")
    dem_table.add_column("Odds", style="green")
    for k, v in dem_condidtional_odds.items():
        dem_table.add_row(k, str(v) if v is not None else "-")

    layout.split_row(
        Layout(Panel(party_table, expand=True), name="party", ratio=1),
        Layout(Panel(gop_table, expand=True), name="gop", ratio=1),
        Layout(Panel(dem_table, expand=True), name="dem", ratio=1),
    )

    return layout


if __name__ == "__main__":
    pres_dir = "data/market_data/presidential-election-winner-2028"
    gop_dir = "data/market_data/republican-presidential-nominee-2028"
    dem_dir = "data/market_data/democratic-presidential-nominee-2028"
    party_dir = (
        "data/market_data/which-party-wins-2028-us-presidential-election"
    )

    pres_mappings = load_mapping(os.path.join(pres_dir, "mappings.json"))
    gop_mappings = load_mapping(os.path.join(gop_dir, "mappings.json"))
    dem_mappings = load_mapping(os.path.join(dem_dir, "mappings.json"))
    party_mappings = load_mapping(os.path.join(party_dir, "mappings.json"))

    pres_candidates = [
        candidate.split("|")[0].strip()
        for candidate in pres_mappings
        if not candidate.startswith("Person")
    ]
    gop_candidates = [
        candidate.split("|")[0].strip()
        for candidate in gop_mappings
        if not candidate.startswith("Person")
    ]
    dem_candidates = [
        candidate.split("|")[0].strip()
        for candidate in dem_mappings
        if not candidate.startswith("Person")
    ]

    probabilities = party_arb_margin(
        list(set([can for can in pres_candidates if can in dem_candidates])),
        list(set([can for can in pres_candidates if can in gop_candidates])),
        pres_dir,
        party_dir,
    )
    gop_conditional_odds = get_conditional_odds(
        gop_candidates,
        pres_dir,
        gop_dir,
        pres_mappings,
        gop_mappings,
    )
    dem_condidtional_odds = get_conditional_odds(
        dem_candidates,
        pres_dir,
        dem_dir,
        pres_mappings,
        dem_mappings,
    )

    try:
        console = Console()
        with Live(
            render_dashboard(
                probabilities, gop_conditional_odds, dem_condidtional_odds
            ),
            refresh_per_second=2,
            console=console,
        ) as live:
            while True:
                probabilities = party_arb_margin(
                    list(
                        set(
                            [
                                can
                                for can in pres_candidates
                                if can in dem_candidates
                            ]
                        )
                    ),
                    list(
                        set(
                            [
                                can
                                for can in pres_candidates
                                if can in gop_candidates
                            ]
                        )
                    ),
                    pres_dir,
                    party_dir,
                )
                gop_conditional_odds = get_conditional_odds(
                    gop_candidates,
                    pres_dir,
                    gop_dir,
                    pres_mappings,
                    gop_mappings,
                )
                dem_condidtional_odds = get_conditional_odds(
                    dem_candidates,
                    pres_dir,
                    dem_dir,
                    pres_mappings,
                    dem_mappings,
                )
                live.update(
                    render_dashboard(
                        probabilities,
                        gop_conditional_odds,
                        dem_condidtional_odds,
                    )
                )
    except KeyboardInterrupt:
        sys.exit(0)
