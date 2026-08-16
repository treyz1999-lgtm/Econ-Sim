from decimal import Decimal

from backend.tests.api.test_campaign_turns import request
from backend.tests.helpers import end_turn_json


def test_foreign_endpoint_returns_three_configured_actors(asgi_transport) -> None:
    """The API should expose the campaign's persisted foreign-state snapshot."""
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]

    response = request(asgi_transport, "GET", f"/api/campaigns/{campaign_id}/foreign")

    assert response.status_code == 200
    assert len(response.json()["foreign"]["nations"]) == 3


def test_trade_orders_settle_atomically_with_end_turn(asgi_transport) -> None:
    """Exports and imports should be persisted in the completed turn snapshot."""
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]
    payload = end_turn_json()
    payload["trade_orders"] = [
        {
            "nation_id": "northreach",
            "exports": {"food": "10"},
            "imports": {"energy": "2"},
        }
    ]

    response = request(
        asgi_transport,
        "POST",
        f"/api/campaigns/{campaign_id}/turns",
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["turn_report"]["foreign"]["total_export_value"]) > 0
    assert Decimal(body["state"]["resources"]["food"]["exports"]) > 0
    assert Decimal(body["state"]["resources"]["energy"]["imports"]) > 0
    assert Decimal(body["state"]["government"]["foreign_reserves"]) >= 0


def test_duplicate_nation_orders_are_rejected_without_a_turn(asgi_transport) -> None:
    """A nation may receive one order only, preserving unambiguous settlement."""
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]
    payload = end_turn_json()
    payload["trade_orders"] = [
        {"nation_id": "northreach", "exports": {"food": "1"}},
        {"nation_id": "northreach", "imports": {"energy": "1"}},
    ]

    rejected = request(
        asgi_transport,
        "POST",
        f"/api/campaigns/{campaign_id}/turns",
        json=payload,
    )
    current = request(asgi_transport, "GET", f"/api/campaigns/{campaign_id}")

    assert rejected.status_code == 422
    assert current.json()["state"]["turn"] == 0
