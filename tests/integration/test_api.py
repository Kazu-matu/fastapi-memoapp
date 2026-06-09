import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest
import pytest_asyncio

BASE = "/api/memos"

MEMO_PAYLOAD = {
    "title": "テストメモ",
    "description": "テスト詳細",
    "status": {"priority": "高", "due_date": None, "is_completed": False},
}


# ---- IT-01: 正常登録 ----
@pytest.mark.asyncio
async def test_create_memo_success(client):
    res = await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    assert res.status_code == 201
    assert res.json()["message"] == "メモが正常に登録されました"


# ---- IT-02: title が空 ----
@pytest.mark.asyncio
async def test_create_memo_empty_title(client):
    payload = {**MEMO_PAYLOAD, "title": ""}
    res = await client.post(f"{BASE}/", json=payload)
    assert res.status_code == 422


# ---- IT-03: title が未指定 ----
@pytest.mark.asyncio
async def test_create_memo_missing_title(client):
    payload = {"description": "詳細", "status": {"priority": "低"}}
    res = await client.post(f"{BASE}/", json=payload)
    assert res.status_code == 422


# ---- IT-04: description が空でも登録成功 ----
@pytest.mark.asyncio
async def test_create_memo_empty_description(client):
    payload = {**MEMO_PAYLOAD, "description": ""}
    res = await client.post(f"{BASE}/", json=payload)
    assert res.status_code == 201


# ---- IT-05: 0件取得 ----
@pytest.mark.asyncio
async def test_get_memos_empty(client):
    res = await client.get(f"{BASE}/")
    assert res.status_code == 200
    assert res.json() == []


# ---- IT-06: 複数件取得 ----
@pytest.mark.asyncio
async def test_get_memos_multiple(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    await client.post(f"{BASE}/", json={**MEMO_PAYLOAD, "title": "2件目"})
    res = await client.get(f"{BASE}/")
    assert res.status_code == 200
    assert len(res.json()) == 2


# ---- IT-07: 存在するIDで1件取得 ----
@pytest.mark.asyncio
async def test_get_memo_by_id_found(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    memos = (await client.get(f"{BASE}/")).json()
    memo_id = memos[0]["memo_id"]
    res = await client.get(f"{BASE}/{memo_id}")
    assert res.status_code == 200
    assert res.json()["title"] == MEMO_PAYLOAD["title"]


# ---- IT-08: 存在しないIDで404 ----
@pytest.mark.asyncio
async def test_get_memo_by_id_not_found(client):
    res = await client.get(f"{BASE}/9999")
    assert res.status_code == 404
    assert res.json()["detail"] == "メモが見つかりません"


# ---- IT-09: 正常更新 ----
@pytest.mark.asyncio
async def test_update_memo_success(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    memo_id = (await client.get(f"{BASE}/")).json()[0]["memo_id"]
    updated = {**MEMO_PAYLOAD, "title": "更新済みタイトル"}
    res = await client.put(f"{BASE}/{memo_id}", json=updated)
    assert res.status_code == 200
    assert res.json()["message"] == "メモが正常に更新されました"
    detail = (await client.get(f"{BASE}/{memo_id}")).json()
    assert detail["title"] == "更新済みタイトル"


# ---- IT-10: 存在しないIDを更新で404 ----
@pytest.mark.asyncio
async def test_update_memo_not_found(client):
    res = await client.put(f"{BASE}/9999", json=MEMO_PAYLOAD)
    assert res.status_code == 404
    assert res.json()["detail"] == "更新対象が見つかりません"


# ---- IT-11: 正常削除（論理削除） ----
@pytest.mark.asyncio
async def test_delete_memo_success(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    memo_id = (await client.get(f"{BASE}/")).json()[0]["memo_id"]
    res = await client.delete(f"{BASE}/{memo_id}")
    assert res.status_code == 200
    assert res.json()["message"] == "メモが正常に削除されました"


# ---- IT-12: 存在しないIDを削除で404 ----
@pytest.mark.asyncio
async def test_delete_memo_not_found(client):
    res = await client.delete(f"{BASE}/9999")
    assert res.status_code == 404
    assert res.json()["detail"] == "削除対象が見つかりません"


# ---- IT-13: 削除後に同IDを取得すると404（論理削除で非表示） ----
@pytest.mark.asyncio
async def test_get_deleted_memo(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    memo_id = (await client.get(f"{BASE}/")).json()[0]["memo_id"]
    await client.delete(f"{BASE}/{memo_id}")
    res = await client.get(f"{BASE}/{memo_id}")
    assert res.status_code == 404


# ---- IT-14: 登録後に履歴が1件作成される ----
@pytest.mark.asyncio
async def test_history_created_on_insert(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    memo_id = (await client.get(f"{BASE}/")).json()[0]["memo_id"]
    res = await client.get(f"{BASE}/{memo_id}/histories")
    assert res.status_code == 200
    histories = res.json()
    assert len(histories) == 1
    assert histories[0]["action"] == "CREATE"


# ---- IT-15: 更新後に履歴が累積される ----
@pytest.mark.asyncio
async def test_history_accumulated_on_update(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    memo_id = (await client.get(f"{BASE}/")).json()[0]["memo_id"]
    await client.put(f"{BASE}/{memo_id}", json={**MEMO_PAYLOAD, "title": "更新後"})
    res = await client.get(f"{BASE}/{memo_id}/histories")
    assert res.status_code == 200
    histories = res.json()
    assert len(histories) == 2
    actions = [h["action"] for h in histories]
    assert "CREATE" in actions
    assert "UPDATE" in actions


# ---- IT-16: 削除後に履歴に DELETE が記録される ----
@pytest.mark.asyncio
async def test_history_delete_recorded(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    memo_id = (await client.get(f"{BASE}/")).json()[0]["memo_id"]
    await client.delete(f"{BASE}/{memo_id}")
    res = await client.get(f"{BASE}/{memo_id}/histories")
    assert res.status_code == 200
    actions = [h["action"] for h in res.json()]
    assert "DELETE" in actions


# ---- IT-17: created_by / updated_by が設定される ----
@pytest.mark.asyncio
async def test_audit_fields_populated(client):
    await client.post(f"{BASE}/", json=MEMO_PAYLOAD)
    memo = (await client.get(f"{BASE}/")).json()[0]
    assert memo["created_by"] != "" and memo["created_by"] is not None
    assert memo["updated_by"] != "" and memo["updated_by"] is not None
