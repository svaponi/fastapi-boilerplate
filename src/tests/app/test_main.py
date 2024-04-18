def test_root(client):
    res = client.get("/foobar")
    print(f"{res.request.method} {res.url} >> {res.status_code} {res.text}")
    assert res.status_code == 404
