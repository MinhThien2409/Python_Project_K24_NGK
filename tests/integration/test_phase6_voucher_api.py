from tests.integration.test_customer_thanh_toan_api import _dung_cu, _login, _payload

def test_customer_cannot_manage_voucher(customer_client):
    client,_=_dung_cu(customer_client);_login(client)
    r=client.get("/api/voucher")
    assert r.status_code==403

def test_checkout_ignores_client_discount_and_total(customer_client):
    client,_=_dung_cu(customer_client);_login(client)
    payload=_payload()
    payload["Discount"]=999999999
    payload["TotalAmount"]=1
    r=client.post("/api/don-hang/dat-hang",json=payload)
    assert r.json["status"] is True
    oid=r.json["data"]["order_ids"][0]
    invoice=client.get("/api/don-hang/hoa-don/%s"%oid).json["data"]
    assert invoice["DiscountAmount"]==0
    assert invoice["TotalAmount"]==225000

def test_voucher_preview_requires_active_session(customer_client):
    client,_=_dung_cu(customer_client)
    r=client.post("/api/voucher/kiem-tra",json={"voucherCode":"SAVE10","Items":[{"ProductId":1,"Quantity":1}]})
    assert r.status_code==403
