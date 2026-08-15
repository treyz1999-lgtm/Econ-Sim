import asyncio
from uuid import uuid4

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.persistence.models import TurnSnapshotModel
from backend.tests.helpers import end_turn_json


def request(
    transport: httpx.ASGITransport, method: str, path: str, **kwargs
) -> httpx.Response:
    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_create_campaign_and_complete_turn_atomically(
    asgi_transport: httpx.ASGITransport,
    session_factory: sessionmaker[Session],
) -> None:
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]

    completed = request(
        asgi_transport,
        "POST",
        f"/api/campaigns/{campaign_id}/turns",
        json=end_turn_json(0),
    )

    assert created.status_code == 201
    assert completed.status_code == 200
    assert completed.json()["state"]["turn"] == 1
    assert completed.json()["dashboard"]["turn"] == 1
    assert completed.json()["dashboard"]["population"]["total"]
    assert completed.json()["dashboard"]["government"]["tax_revenue"]
    assert completed.json()["turn_report"]["turn"] == 1
    with session_factory() as session:
        snapshot_count = session.scalar(select(func.count(TurnSnapshotModel.id)))
    assert snapshot_count == 2


def test_stale_turn_is_rejected_without_snapshot(
    asgi_transport: httpx.ASGITransport,
    session_factory: sessionmaker[Session],
) -> None:
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]

    stale = request(
        asgi_transport,
        "POST",
        f"/api/campaigns/{campaign_id}/turns",
        json=end_turn_json(1),
    )

    assert stale.status_code == 409
    with session_factory() as session:
        snapshot_count = session.scalar(select(func.count(TurnSnapshotModel.id)))
    assert snapshot_count == 1


def test_overallocated_turn_is_rejected_without_snapshot(
    asgi_transport: httpx.ASGITransport,
    session_factory: sessionmaker[Session],
) -> None:
    created = request(asgi_transport, "POST", "/api/campaigns", json={"seed": 42})
    campaign_id = created.json()["state"]["campaign_id"]
    payload = end_turn_json(0)
    payload["labor_allocation"]["agriculture"] = {"farmers": {"children": "31"}}

    invalid = request(
        asgi_transport,
        "POST",
        f"/api/campaigns/{campaign_id}/turns",
        json=payload,
    )

    assert invalid.status_code == 422
    with session_factory() as session:
        snapshot_count = session.scalar(select(func.count(TurnSnapshotModel.id)))
    assert snapshot_count == 1


def test_unknown_campaign_returns_not_found(
    asgi_transport: httpx.ASGITransport,
) -> None:
    response = request(
        asgi_transport,
        "POST",
        f"/api/campaigns/{uuid4()}/turns",
        json=end_turn_json(0),
    )

    assert response.status_code == 404
