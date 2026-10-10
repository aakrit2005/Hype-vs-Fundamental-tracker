from app.models.ticker import Ticker


async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200


async def test_healthz(client):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_register_login_me(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "judge@example.com", "password": "password123"},
    )

    assert response.status_code == 201

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "judge@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "judge@example.com"


async def test_watchlist_requires_auth(client):
    response = await client.get("/api/v1/watchlist")
    assert response.status_code == 401


async def test_watchlist_flow(client, session):
    session.add(Ticker(symbol="AAA", name="Alpha", sector="Technology"))
    await session.commit()

    from sqlalchemy import select

    result = await session.execute(select(Ticker))
    ticker = result.scalar_one()

    await client.post(
        "/api/v1/auth/register",
        json={"email": "watch@example.com", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "watch@example.com", "password": "password123"},
    )

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/v1/watchlist",
        json={"ticker_id": ticker.id},
        headers=headers,
    )

    assert response.status_code == 201

    response = await client.get("/api/v1/watchlist", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await client.delete(
        f"/api/v1/watchlist/{ticker.id}",
        headers=headers,
    )

    assert response.status_code == 204

    response = await client.get("/api/v1/watchlist", headers=headers)
    assert response.json() == []


async def test_leaderboard_empty(client):
    response = await client.get("/api/v1/signals/leaderboard")
    assert response.status_code == 200
    assert response.json() == []


async def test_tickers_list(client, session):
    session.add_all(
        [
            Ticker(symbol="AAA", name="Alpha", sector="Technology"),
            Ticker(symbol="BBB", name="Beta", sector="Technology"),
        ]
    )

    await session.commit()

    response = await client.get("/api/v1/tickers")
    assert response.status_code == 200
    assert len(response.json()) == 2