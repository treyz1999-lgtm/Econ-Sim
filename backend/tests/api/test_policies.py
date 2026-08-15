from backend.tests.api.test_campaign_turns import request
from backend.tests.helpers import end_turn_json


def test_policy_catalog_reports_active_and_blocked_choices(asgi_transport) -> None:
    """The campaign catalog should explain active policies and eligibility blockers."""
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]

    response = request(asgi_transport, "GET", f"/api/campaigns/{campaign_id}/policies")

    assert response.status_code == 200
    policies = {item["definition"]["id"]: item for item in response.json()["policies"]}
    assert policies["barter"]["active"] is True
    assert policies["commodity_currency"]["eligible"] is True
    assert "prerequisites_not_met" in policies["income_tax"]["blockers"]


def test_policy_adoption_is_part_of_atomic_end_turn(asgi_transport) -> None:
    """A valid policy action should persist with the same snapshot as its turn."""
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]
    payload = end_turn_json()
    payload["policy_adoption"] = {"policy_id": "commodity_currency"}

    response = request(
        asgi_transport,
        "POST",
        f"/api/campaigns/{campaign_id}/turns",
        json=payload,
    )

    assert response.status_code == 200
    assert (
        response.json()["turn_report"]["policy"]["adopted_policy"]
        == "commodity_currency"
    )
    assert response.json()["state"]["policies"]["pending"]["activation_turn"] == 2


def test_invalid_policy_adoption_does_not_advance_turn(asgi_transport) -> None:
    """An ineligible policy must fail without creating a completed turn."""
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]
    payload = end_turn_json()
    payload["policy_adoption"] = {"policy_id": "income_tax"}

    rejected = request(
        asgi_transport,
        "POST",
        f"/api/campaigns/{campaign_id}/turns",
        json=payload,
    )
    state = request(asgi_transport, "GET", f"/api/campaigns/{campaign_id}")

    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "prerequisites_not_met"
    assert state.json()["state"]["turn"] == 0
