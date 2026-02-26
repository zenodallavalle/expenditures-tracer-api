def test_get_users_wo_authentication_fails(client):
    response = client.get("/v3/users/")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Authentication credentials were not provided."
