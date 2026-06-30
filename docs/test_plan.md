# Test Plan — Single Bet Placement


## TC-01 — [Positive][UI] Place a single bet end-to-end
**Priority:** Critical

**Risk Rationale:** This is the core revenue journey and the only way a user
makes money move; if it breaks, the product's primary function is unusable. It
also exercises the full money chain (selection → stake → payout calc → stake
deduction → receipt), making it the highest-value single check.

| # | Step | Expected Result                                                                                                                             |
| --- | --- |---|
| 1 | Open the app with a valid `user-id`. | Match list shows upcoming matches; header balance shows €120.00.                                                                            |
| 2 | Click an odds button (e.g. HOME) on an upcoming match. | The selection appears in the bet slip with match, selection, and odds; exactly one active selection.                                        |
| 3 | Enter a valid stake within balance (e.g. €10). | Potential payout updates to `stake × odds`; "Place Bet" is enabled.                                                                         |
| 4 | Click "Place Bet". | Button shows "Placing…", then resolves to the success receipt modal.                                                                        |
| 5 | Inspect the receipt. | Shows Bet ID, match, selection, stake €10, odds at placement, payout = stake × odds, timestamp; currency EUR.                               |
| 6 | Close the receipt. | Returns to the main flow with no active selection; balance is reduced by the stake (€120.00 → €110.00) and is identical in header and slip. |

---

## TC-02 — [Negative][API] Bet exceeding available funds is rejected
**Priority:** Critical

**Risk Rationale:** The API is the source of truth and must enforce the balance
boundary regardless of the UI; accepting bets above the balance creates
unbacked liabilities and negative balances — a direct financial-integrity and
fraud risk. Boundary case: stake vs remaining balance.

| # | Step | Expected Result |
| --- | --- | --- |
| 1 | `POST /api/reset-balance`. | `200`; balance restored to baseline. |
| 2 | `POST /api/place-bet` with `stake: 100` on an upcoming match. | `200`; balance reduced, leaving < €100 available. |
| 3 | `POST /api/place-bet` again with `stake: 100`. | `422` with an "Insufficient balance" error; no further deduction; balance never goes negative. |

---

## TC-03 — [Negative][API] Negative stake value is rejected
**Priority:** Critical

**Risk Rationale:** A negative stake inverts the money flow (credits the user),
so failing to reject it is a direct fraud vector. Boundary/validation case
immediately below the positive-stake domain.

| # | Step | Expected Result |
| --- | --- | --- |
| 1 | `POST /api/reset-balance`. | `200`; baseline balance noted. |
| 2 | `POST /api/place-bet` with `stake: -5`. | `422` with "Stake must be a positive number" (or equivalent); bet not accepted. |
| 3 | `GET /api/balance`. | Balance unchanged from baseline — no credit applied. |

---

## TC-04 — [Negative][UI] Insufficient funds is blocked at the UI
**Priority:** High

**Risk Rationale:** The UI must guard the balance boundary so users get clear,
immediate feedback and cannot submit unaffordable bets; this is the UX-layer
counterpart to TC-02 (defense in depth). Boundary case at available balance.

| # | Step | Expected Result |
| --- | --- | --- |
| 1 | Reset balance (precondition). | Balance shows €125.50. |
| 2 | Place a bet that draws the balance down (e.g. €100). | Bet succeeds; displayed balance becomes €25.50. |
| 3 | Select an outcome and enter a stake above the remaining balance (e.g. €100 > €25.50). | UI shows "Insufficient balance" and disables/blocks "Place Bet". |
| 4 | Attempt to place the bet anyway. | Placement is prevented; no deduction occurs; balance stays €25.50. |

---

## TC-05 — [Negative][UI] Repeat bet on the same match is prevented
**Priority:** High

**Risk Rationale:** The spec scopes the feature to single bets only (no
accumulators/multi-bets). Allowing a second active bet on the same match
violates that constraint and can drive undefined backend behaviour and
unintended exposure.

| # | Step | Expected Result |
| --- | --- | --- |
| 1 | Place a valid bet on a match (per TC-01). | Bet placed; success receipt shown. |
| 2 | Return to the match list and attempt to select odds on the same match again. | The match's odds buttons are disabled (or selection is blocked), preventing a second bet on that match. |
| 3 | Attempt the placement via the slip if reachable. | Placement is rejected (UI guard; backend returns `409` for a duplicate in-progress/placed bet). |

---

## TC-06 — [Negative][UI] Placement failure shows the error modal and Rebet recovers
**Priority:** Medium

**Risk Rationale:** Backend/network failures are inevitable; the app must fail
safely — surface the error modal, avoid deducting the stake, and let the user
recover via Rebet without double-charging. Validates §2.3/§2.5 failure handling
and state integrity under fault.

| # | Step | Expected Result |
| --- | --- | --- |
| 1 | Select an outcome and enter a valid stake. | Slip is ready; potential payout computed. |
| 2 | Disable the network connection (DevTools offline / Wi-Fi off). | Failure precondition is in place. |
| 3 | Click "Place Bet". | Shows "Placing…", then an error modal titled "Something went wrong" with a retry option; the stake is **not** deducted. |
| 4 | Re-enable the network and click "Rebet". | Modal closes and placement retries; on success the receipt appears and the stake is deducted exactly once. |
| 5 | (Alternative path) Click "Close" or the top-right ✕ instead of Rebet. | Modal closes, the current selection/stake is cleared, and no deduction occurs. |
