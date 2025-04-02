import os

from fastapi.testclient import TestClient

from main import app


def test_full_flow():
    if os.getenv("ENVIRONMENT") != "development":
        print("Skipping tests as the environment is not development.")
        return

    client = TestClient(app)

    # Verify the valid login
    login_response = client.post(
        "/login",
        data={
            "username": "leandro@gmail.com",
            "password": "123456789",
            "grant_type": "password",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    print(f"✅ Test Login: OK \nToken: {token}")

    # Verify the token
    token_response = client.post("/token", headers={"Authorization": f"Bearer {token}"})
    assert token_response.status_code == 200
    assert token_response.json()["user"] == "leandro@gmail.com"
    print("✅ Test valid Token: OK")

    # Verify the invalid login
    invalid_response = client.post(
        "/token", headers={"Authorization": "Bearer invalid_token"}
    )
    assert invalid_response.status_code == 401
    print("✅ Test invalid Token: OK")


# Automatically run tests when the API starts in development mode
if os.getenv("ENVIRONMENT") == "development":
    test_full_flow()
