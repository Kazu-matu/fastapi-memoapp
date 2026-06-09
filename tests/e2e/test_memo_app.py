"""
E2E テスト（Playwright）
前提: FastAPI サーバーが http://localhost:8000 で起動済み
      Python http.server が http://127.0.0.1:5500 で起動済み

テスト分離:
  各テストの前後に requests で API を直接叩き DB をクリアする
  → UI の非同期タイミングに依存したクリーンアップを排除
"""
import requests
import pytest
from playwright.sync_api import Page, expect

FRONT_URL = "http://127.0.0.1:5500/frontapp/index.html"
API_BASE  = "http://localhost:8000/memos"


def api_clear_all():
    """API 経由で全メモを削除する（テスト前後の DB リセット用）"""
    memos = requests.get(f"{API_BASE}/").json()
    for m in memos:
        requests.delete(f"{API_BASE}/{m['memo_id']}")


def row_count(page: Page) -> int:
    return page.locator("#memos tbody tr").count()


def reload_and_wait(page: Page):
    """ページをリロードし一覧の初期表示が完了するまで待つ"""
    page.reload()
    page.wait_for_load_state("networkidle")


@pytest.fixture(autouse=True)
def clean_state(page: Page):
    """各テスト前後に DB をクリアし、ページを最初の状態に戻す"""
    api_clear_all()
    page.goto(FRONT_URL)
    page.wait_for_load_state("networkidle")
    yield
    api_clear_all()


def accept_dialog_and_wait_for_count(page: Page, click_target, expected_count: int):
    """クリック後に出るダイアログを受け付け、一覧が expected_count になるまで待つ"""
    with page.expect_event("dialog") as dialog_info:
        click_target()
    dialog = dialog_info.value
    msg = dialog.message
    dialog.accept()
    page.wait_for_load_state("networkidle")
    page.wait_for_function(
        f"document.querySelectorAll('#memos tbody tr').length === {expected_count}"
    )
    return msg


# ---- E2E-01: メモ新規登録 ----
def test_create_memo(page: Page):
    assert row_count(page) == 0  # DB は空

    page.fill("#title", "E2Eテストメモ")
    page.fill("#description", "Playwright から登録")
    page.select_option("#priority", "高")
    page.fill("#due_date", "2025-12-31")

    msg = accept_dialog_and_wait_for_count(
        page,
        lambda: page.click("#createMemoForm button[type='submit']"),
        expected_count=1,
    )

    assert "登録" in msg, f"予期しないメッセージ: {msg}"
    last_title = page.locator("#memos tbody tr").last.locator("td").first.inner_text()
    assert last_title == "E2Eテストメモ"


# ---- E2E-02: メモ一覧表示 ----
def test_list_memos(page: Page):
    # API で2件登録してからリロード
    requests.post(f"{API_BASE}/", json={"title": "一覧テスト1", "description": "", "status": {"priority": "低"}})
    requests.post(f"{API_BASE}/", json={"title": "一覧テスト2", "description": "", "status": {"priority": "中"}})
    reload_and_wait(page)

    rows = page.locator("#memos tbody tr")
    expect(rows).to_have_count(2)
    titles = [rows.nth(i).locator("td").first.inner_text() for i in range(2)]
    assert "一覧テスト1" in titles
    assert "一覧テスト2" in titles


# ---- E2E-03: メモ編集・更新 ----
def test_edit_memo(page: Page):
    requests.post(f"{API_BASE}/", json={"title": "編集前タイトル", "description": "", "status": {"priority": "低"}})
    reload_and_wait(page)
    assert row_count(page) == 1

    page.locator("#memos tbody tr").first.locator("button.edit").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("#formTitle")).to_have_text("メモの編集")

    page.fill("#title", "編集後タイトル")

    msg = accept_dialog_and_wait_for_count(
        page,
        lambda: page.click("#updateButton"),
        expected_count=1,
    )

    assert "更新" in msg, f"予期しないメッセージ: {msg}"
    title_cell = page.locator("#memos tbody tr").first.locator("td").first.inner_text()
    assert title_cell == "編集後タイトル"


# ---- E2E-04: メモ削除 ----
def test_delete_memo(page: Page):
    requests.post(f"{API_BASE}/", json={"title": "削除対象メモ", "description": "", "status": {"priority": "低"}})
    reload_and_wait(page)
    assert row_count(page) == 1

    msg = accept_dialog_and_wait_for_count(
        page,
        lambda: page.locator("#memos tbody tr").first.locator("button.delete").click(),
        expected_count=0,
    )

    assert "削除" in msg, f"予期しないメッセージ: {msg}"
    expect(page.locator("#memos tbody tr")).to_have_count(0)


# ---- E2E-05: title 未入力バリデーション ----
def test_create_memo_empty_title(page: Page):
    assert row_count(page) == 0

    page.fill("#title", "")
    page.fill("#description", "詳細のみ")
    page.click("#createMemoForm button[type='submit']")
    page.wait_for_timeout(800)

    # HTML バリデーションにより送信されず件数変わらず
    expect(page.locator("#memos tbody tr")).to_have_count(0)
