# Critical severity
---

## BUG-001 — Negative stake is accepted via API, increasing the user's balance

**Severity:** Critical

**Reproduction Steps**
1. Reset the balance: `curl -s -X POST "https://qae-assignment-tau.vercel.app/api/reset-balance" -H "x-user-id: <USER_ID>"`.
2. Place a bet with `-5` stake:
   `curl -s -X POST "https://qae-assignment-tau.vercel.app/api/place-bet" -H "x-user-id: <USER_ID>" -H "Content-Type: application/json" -d '{"matchId":"premier-league-liverpool-man-city-2026-07-02","selection":"HOME","stake":-5}'`.
3. Re-check the balance: `curl -s "https://qae-assignment-tau.vercel.app/api/balance" -H "x-user-id: <USER_ID>"` → `125`.

**Expected vs Actual**
- **Expected:** [API] - `POST /place-bet` returns `422` with error message "Stake must be a positive number."
- **Actual:** `POST /place-bet` returns 200. Bet is actually accepted. Balance increased by €5.

**Business Impact:** Direct fraud vector — a user can inflate their balance arbitrarily with negative-stake bets.

**Evidence:** See [bet_negative.png](bug_screenshots/bet_negative.png) with successful Bet response.

---


## BUG-002 — /place-bet dosn't check for funds sufficiency 

**Severity:** Critical

**Reproduction Steps**
1. Place a bet with `100` stake:
   `curl -s -X POST "https://qae-assignment-tau.vercel.app/api/place-bet" -H "x-user-id: <USER_ID>" -H "Content-Type: application/json" -d '{"matchId":"premier-league-liverpool-man-city-2026-07-02","selection":"HOME","stake":100}'`.
2. Repeat step 1.

- **Expected:** `422` "Insufficient balance" returned. 
- **Actual:** `200` returned. Bet is placed. Balance is negative

**Business Impact:** Direct fraud vector - Users can make unlimited number of debts which are not backed by funds on Balance.

**Evidence:** See [api_negative_balance.png](bug_screenshots/api_negative_balance.png).

---


## BUG-003 — It is possible to place a bet on match in the Past (both UI and API)

**Severity:** Critical

**Reproduction Steps**
1. Click any of odds for a match in the Past. For example `Manchester Utd - Chelsea` dated `Fri, Feb 27`.
2. Set a Bet Stake.
3. Click `PLACE BET`.

**Expected vs Actual**
- **Expected:**
1. Past Matches aren't displayed  
2. [API] - `POST /place-bet` returns `422` with error message stating that betting on Past matches not allowed.
- **Actual:** 
1. [UI] - Past matches are displayed
2. [API] - `POST /place-bet` returns 200. Bet is actually accepted. Balance decreased.

**Business Impact:** Either direct fraud vector in case User receive Payout or a legal complain from the User if Payout is not received.

**Evidence:** See [bet_the_past.png](bug_screenshots/bet_the_past.png) with successful Bet.

---



# High severity
---

## BUG-004 — HOME<->AWAY teams are inverted on Bet Receipt

**Severity:** High

**Reproduction Steps**
1. Place a bet for any Match.
2. Observe Bet Receipt.

- **Expected:** Teams are mentioned according to HOME -> AWAY order.
- **Actual:** Order is inverted.

**Business Impact:** Introduces confusion for User regarding which team they actully bet on.  

**Evidence:** See [home_away_inverted.png](bug_screenshots/home_away_inverted.png).

---

## BUG-005 — Multiple Bets for the same Match allowed on both UI and API

**Severity:** High

**Reproduction Steps**
1. Place a bet for any Match.
2. Place new Bet for the same Match.

- **Expected:** 
1. [UI] Odds buttons for the Match are disabled after placing a Bet.
2. [API] /place-bet returns `409` with message informing the multiple Bets for the same Match not allowed. 
- **Actual:** Muptiple Bets for same Match placed.

**Business Impact:** `Single Bet Placement` spec -> `1. Feature Overview` defines that `Multi-bets/accumulators` aren't supported. Which in turn means that backend may provide unexpected results in this case. 

**Evidence:** See [multi-bet.png](bug_screenshots/multi-bet.png).

---


## BUG-006 — Balance is not updated on UI automatically

**Severity:** High

**Reproduction Steps**
1. Reset Balance.
2. Place a bet with `100` stake via UI.

- **Expected:** Balance is dispalyed as `20`.
- **Actual:** Balance not updated - still `120`. UI allows to send another Bet request with Stake >20. Also note that due to BUG-002 next Bet is accepted and User goes into negative Balance.

**Business Impact:** Not as Critical as BUG-002. Still High severity since it misleading about available funds.

**Evidence:** See [ui_negative_balance.png](bug_screenshots/ui_negative_balance.png).

---


## BUG-007 — Potential Payout on UI is different from the one returned by API 

**Severity:** High

**Reproduction Steps**
1. Place a Bet with `€10` Stake and `4.50` Odds.
2. Observe `Potential Payout` value on Bet success modal.

**Expected vs Actual**
- **Expected:** `€45.00`.
- **Actual:** `€20.00` while API returns correct number.

**Business Impact:** Data in DB is not corrupted still it breaks Users trust in product money-handling capabilities.

**Evidence:** See [payout_ui.png](bug_screenshots/payout_ui.png) with UI and API response.

---


# Medium severity
---

## BUG-008 — /place-bet resturns balance in USD

**Severity:** Medium

**Reproduction Steps**
1. Place a bet and observe /place-bet response JSON.

**Expected vs Actual**
- **Expected:** `"currency":"EUR"`
- **Actual:** `"currency":"USD"`

**Business Impact:** The success receipt shows the wrong currency, misleading users about stake/payout and raising a compliance concern for a money-handling product. May become a critical issue once we add multi-currency.

**Evidence:** See [bet_currency_usd.png](bug_screenshots/bet_currency_usd.png) with response.

---


## BUG-009 — `reset-balance` response disagrees with persisted balance (restores wrong amount)

**Severity:** Medium

**Reproduction Steps**
1. Reset: `curl -s -X POST "https://qae-assignment-tau.vercel.app/api/reset-balance" -H "x-user-id: <USER_ID>"` → body reports `balance: 125.5`.

**Expected vs Actual**
- **Expected:** `"balance":120`
- **Actual:** `"balance":125.5` Note that actual balance in DB is `120`

**Business Impact:** No direct business impact since `/reset-balance` should not be exposed to Users. Still it introduces confusion during test cases creation.

**Evidence:** See [reset_wrong_balance.png](bug_screenshots/reset_wrong_balance.png) with response.

---


## BUG-010 — Malformed JSON body returns `500` instead of `400`

**Severity:** Medium

**Reproduction Steps**
1. Send a malformed JSON body:
   `curl -s -o /dev/null -w "%{http_code}\n" -X POST "https://qae-assignment-tau.vercel.app/api/place-bet" -H "x-user-id: <USER_ID>" -H "Content-Type: application/json" --data '{not json'`.

**Expected vs Actual**
- **Expected:** `400` malformed-payload error.
- **Actual:** `500 internal_server_error` — "Unable to process request."

**Business Impact:** Robustness/observability gap — client errors surfacing as server errors mask real outages and pollute alerting.

**Evidence:** See [500_on_malformed_json.png](bug_screenshots/500_on_malformed_json.png) with response.

---


# Low severity
---

## BUG-011 — Unsupported HTTP method on `/place-bet` returns `200` instead of `405`

**Severity:** Low

**Reproduction Steps**
1. Call the endpoint with an unsupported method (HTTP GET):
   `curl -s -o /dev/null -w "%{http_code}\n" "https://qae-assignment-tau.vercel.app/api/place-bet" -H "x-user-id: <USER_ID>"`.

**Expected vs Actual**
- **Expected:** `405 method not allowed`.
- **Actual:** `200 OK` with empty body `{}`.

**Business Impact:** Protocol-hygiene issue that misleads API consumers and hides routing/method-handling mistakes; no direct user impact.

**Evidence:** See [200_instead_of_405.png](bug_screenshots/200_instead_of_405.png) with response.

---


## BUG-012 — Single Bet Placement specification (PRD) ambiguity — minimum stake €1.00 vs €1.01

**Severity:** Low

**Reproduction Steps**
1. Check `3 - Business Rules` table -> `Stake min (per bet)`
2. Check `4 - Validation Rules`  -> `4.1 - Stake Validation (UI and API)` -> `Stake`

- **Expected:** `€1.00` in both cases.
- **Actual:** §4.1 = `€1.01 (positive values)`

**Business Impact:** No as of now. Implemented as `€1.00` (inclusive)

**Evidence:** See [spec_min_stake.png](bug_screenshots/spec_min_stake.png).

---


## BUG-013 — Selection is not displayed on Bet success modal

**Severity:** Low

**Reproduction Steps**
1. Place a bet for any Match.

- **Expected:** Selection is displayed as one of [<name_of_team_1>, DRAW, <name_of_team_2>]
- **Actual:** Not displayed on modal.

**Business Impact:** Users may be confused and spending extra steps to double-check their Bet. 

**Evidence:** See [ui_no_selection.png](bug_screenshots/ui_no_selection.png).

---


## BUG-014 — Matches number on UI doesn't reflect actual filtered count

**Severity:** Low

**Reproduction Steps**
1. Open Match List and select Jun'1-Jun'1 in Calendar.

- **Expected:** "Showing 1 match" is displayed in header
- **Actual:** "Showing 103 matches" in header.

**Business Impact:** No major impact.

**Evidence:** See [ui_matches_count.png](bug_screenshots/ui_matches_count.png).

---


## BUG-015 — spec ambiguity - kick-off time label is expected but not defined in API

**Severity:** Low

**Reproduction Steps**
1. Open Match List.

- **Expected:** According to `2.1 Match Lis` each Match has kickoff date/time label
- **Actual:** Date is there but time is missing. According to `5.3 Endpoints` `kickoffDate: string ( YYYY-MM-DD )` which means there is no way to specify exact time.

**Business Impact:** No major impact.

**Evidence:** .

---


## BUG-016 — spec - `Remove All` is misleading

**Severity:** Low

**Reproduction Steps**
1. See spec `2.2 Bet Slip`

- **Expected:** UX of cancelling Bet in not ambiguous. `Cancel` is an example of unambigous button label here.
- **Actual:** `Remove All` is misleading as it may be understood since there is only 1 Bet slip.

**Business Impact:** No major impact.

**Evidence:** .