"""Shared pytest fixtures.

Provides:
* ``api`` — a session-scoped :class:`BettingClient`.
* ``driver`` — a function-scoped Chrome WebDriver (headless by default).
* ``reset_balance`` — side-effect fixture that restores the user's starting
  balance for test isolation, using POST /api/reset-balance (spec §5.3).
* ``verify`` — soft assertion that also renders as an Allure step.
* ``upcoming_match`` — earliest upcoming :class:`Match` (deterministic data).
"""

from __future__ import annotations

import allure
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from api.betting_client import BettingClient
from config import settings
from utils.matches import Match, earliest_upcoming_match


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run the browser with a visible UI (overrides HEADLESS=true).",
    )


@pytest.fixture(scope="session")
def api() -> BettingClient:
    """A reusable API client pointed at the configured environment."""
    settings.require_user_id()  # fail fast with setup guidance if unset
    return BettingClient()


@pytest.fixture
def reset_balance(api: BettingClient) -> None:
    """Reset the user's balance before the test for isolation between runs."""
    response = api.reset_balance()
    assert response.status_code == 200, f"reset-balance precondition failed: {response.status_code} {response.text}"


@pytest.fixture
def upcoming_match(api: BettingClient) -> Match:
    """Earliest upcoming match from the catalogue."""
    matches = [Match.from_api(m) for m in api.get_matches().json()]
    return earliest_upcoming_match(matches)


@pytest.fixture
def driver(request: pytest.FixtureRequest):
    settings.require_user_id()  # UI auth needs ?user-id=; fail fast if unset
    options = Options()
    headed = request.config.getoption("--headed")
    if settings.HEADLESS and not headed:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={settings.BROWSER_WINDOW_SIZE}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)  # rely on explicit waits only
    yield driver
    driver.quit()


@pytest.fixture
def verify(check, request):
    """Soft assertion that also shows up as its own Allure step."""

    def _verify(description: str, passed: bool) -> bool:
        check.is_true(passed, msg=description)
        try:
            with allure.step(description):
                if not passed:
                    """Attach a screenshot + page source to the Allure report on each UI failure."""
                    driver = request.node.funcargs.get("driver")
                    if driver is not None:
                        allure.attach(
                            driver.get_screenshot_as_png(),
                            name=f"screenshot — {description}",
                            attachment_type=allure.attachment_type.PNG,
                        )
                        allure.attach(
                            driver.page_source,
                            name="page-source",
                            attachment_type=allure.attachment_type.HTML,
                        )
                    raise AssertionError(description)
        except AssertionError:
            pass
        return passed

    return _verify
