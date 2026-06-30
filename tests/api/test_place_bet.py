"""Single parametrized test_invalid_stake_is_rejected() verifies boundary values, equivalence
partitioning, and type checks for the `stake` field. This allows to cover a range of regression risks
for a critical field in the /place-bet API endpoint.

Known defect: BUG-001 — /place-bet accepts negative stakes (credits balance).
"""

from __future__ import annotations

from typing import Any

import pytest

from api.schemas import ERROR_ENVELOPE_FIELDS, ErrorCode
from utils.money import decimal_from_float

OMIT = object()


STAKE_REJECTED = [
    pytest.param(0.99, 422, ErrorCode.INVALID_STAKE_MIN, id="below-min-0.99"),
    pytest.param(100.01, 422, ErrorCode.INVALID_STAKE_MAX, id="above-max-100.01"),
    pytest.param(0, 422, ErrorCode.INVALID_STAKE_MIN, id="zero"),
    pytest.param(1000000, 422, ErrorCode.INVALID_STAKE_MAX, id="far-above-max"),
    pytest.param(1.005, 422, ErrorCode.INVALID_STAKE_PRECISION, id="too-many-decimals"),
    pytest.param(-5, 422, ErrorCode.INVALID_STAKE_MIN, id="negative-whole", marks=pytest.mark.known_bug("BUG-001")),
    pytest.param(
        -0.01, 422, ErrorCode.INVALID_STAKE_MIN, id="negative-fraction", marks=pytest.mark.known_bug("BUG-001")
    ),
    pytest.param("abc", 422, ErrorCode.INVALID_STAKE_TYPE, id="non-numeric-string"),
    pytest.param(None, 422, ErrorCode.INVALID_STAKE_TYPE, id="null"),
    pytest.param(True, 422, ErrorCode.INVALID_STAKE_TYPE, id="boolean"),
    pytest.param("", 422, ErrorCode.INVALID_STAKE_TYPE, id="empty-string"),
    pytest.param(OMIT, 422, ErrorCode.INVALID_STAKE_TYPE, id="field-missing"),
]


@pytest.mark.api
@pytest.mark.parametrize("stake, expected_status, expected_error", STAKE_REJECTED)
def test_invalid_stake_is_rejected(api, reset_balance, upcoming_match, stake, expected_status, expected_error):
    baseline = decimal_from_float(api.get_balance().json()["balance"])

    body: dict[str, Any] = {"matchId": upcoming_match.id, "selection": "HOME"}
    if stake is not OMIT:
        body["stake"] = stake
    response = api.place_bet_raw(body)

    assert response.status_code == expected_status, response.text
    body_json = response.json()
    assert set(body_json) == ERROR_ENVELOPE_FIELDS, (
        f"rejection envelope must be exactly {set(ERROR_ENVELOPE_FIELDS)}: {response.text}"
    )
    assert body_json.get("error") == expected_error, f"wrong error code: {response.text}"
    assert body_json.get("message") == expected_error.message, f"wrong message: {response.text}"
    assert decimal_from_float(api.get_balance().json()["balance"]) == baseline, (
        "rejected bet must not change the balance"
    )
