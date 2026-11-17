def test_signup_page_is_accessible(web_client):
    response = web_client.get("/")

    assert response.status_code == 200
    assert b"Sign up" in response.data