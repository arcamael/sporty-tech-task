"""TC-01: place a single bet (the critical happy path).

WHY THIS TEST: Placing a single bet is the product's core revenue journey and
the highest-value thing to protect. It exercises the full money chain in one
flow — match selection, stake entry, live payout computation, placement, the
success receipt, and the resulting balance change.

Every verification asserts the *spec-correct* expectation via
the ``verify`` soft-assert helper, so a single run reports ALL deviations at
once. Each verification is a flat, top-level Allure step (red on failure), so
failures are visible without expanding anything. Money is compared as ``Decimal``
for exact equality (no float tolerance). Known defects are surfaced rather than
skipped:
  * BUG-004 — receipt inverts home/away teams
  * BUG-006 — UI balance not refreshed after placement
  * BUG-007 — receipt payout != stake×odds
  * BUG-013 — receipt omits the Selection field
"""

from __future__ import annotations

from decimal import Decimal

import allure
import pytest

from config import settings
from pages.bet_slip_page import BetSlipPage
from pages.match_list_page import MatchListPage
from pages.receipt_modal import SuccessReceipt
from utils.money import decimal_from_float


@pytest.mark.ui
def test_place_single_bet_happy_path(driver, api, reset_balance, verify, upcoming_match):
    stake = Decimal("10.00")
    outcome = "HOME"
    start_balance = Decimal(settings.STARTING_BALANCE)

    match = upcoming_match
    odds = match.odds_for(outcome)
    expected_payout = stake * odds
    teams_label = match.teams_label

    match_list = MatchListPage(driver)
    bet_slip = BetSlipPage(driver)
    receipt = SuccessReceipt(driver)

    match_list.load()
    verify("Header balance matches the account balance", match_list.header_balance() == start_balance)
    verify("Bet-slip balance matches the header balance", bet_slip.balance() == start_balance)

    match_list.select_outcome(match.id, outcome)
    verify("Selection added to bet slip", bet_slip.has_selection())
    verify("Bet slip shows the selected match teams", match.home_team in bet_slip.selection_teams())
    verify("Bet slip shows the selected outcome (Home)", "Home" in bet_slip.selection_market())
    verify("Bet slip odds match the match odds", bet_slip.selection_odds() == odds)
    verify("Place Bet is disabled before a stake is entered", not bet_slip.place_bet_enabled())

    bet_slip.enter_stake(stake)
    verify("Total stake equals the entered stake", bet_slip.total_stake() == stake)
    verify("Slip potential payout equals stake × odds", bet_slip.potential_payout() == expected_payout)
    verify("Place Bet is enabled with a valid stake", bet_slip.place_bet_enabled())

    bet_slip.place_bet()
    receipt.wait_shown()

    verify("Receipt shows a bet id", receipt.bet_id().startswith("#"))
    verify("Receipt lists home team first — BUG-004 (teams inverted)", receipt.match() == teams_label)
    verify("Receipt stake equals the stake", receipt.stake() == stake)
    verify("Receipt odds equal the odds", receipt.odds() == odds)
    verify("Receipt payout equals stake × odds — BUG-007", receipt.payout() == expected_payout)
    verify("Receipt shows the Selection field — BUG-013", "Home" in receipt.body_text())
    verify("Receipt shows a placement timestamp", bool(receipt.placed_at()))

    receipt.close()
    receipt.wait_closed()
    verify("Bet slip is empty after closing the receipt", bet_slip.is_empty())
    expected_after = start_balance - stake
    verify(
        "Server balance is reduced by the stake",
        decimal_from_float(api.get_balance().json()["balance"]) == expected_after,
    )
    verify("Header balance is reduced by the stake — BUG-006", match_list.header_balance() == expected_after)
    verify("Bet-slip balance is reduced by the stake — BUG-006", bet_slip.balance() == expected_after)
