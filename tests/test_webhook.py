import hmac
import hashlib
import base64
import json
import pytest
from fastapi.testclient import TestClient
from main import app, handler

client = TestClient(app)

def create_signature(secret: str, body: str) -> str:
    """計算 LINE Webhook 規範的 HMAC-SHA256 Base64 簽章"""
    hash_bytes = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_bytes).decode("utf-8")

def test_root_endpoint():
    """測試首頁端點"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["webhook_endpoint"] == "/callback"

def test_health_endpoint():
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_callback_missing_signature():
    """測試未提供 X-Line-Signature Header 時應回傳 400"""
    response = client.post("/callback", json={"events": []})
    assert response.status_code == 400
    assert "Missing X-Line-Signature" in response.json()["detail"]

def test_callback_invalid_signature():
    """測試偽造或錯誤的簽章應回傳 400"""
    response = client.post(
        "/callback",
        headers={"X-Line-Signature": "invalid_fake_signature_abc123"},
        content='{"events": []}'
    )
    assert response.status_code == 400
    assert "Invalid signature" in response.json()["detail"]

def test_callback_valid_signature_empty_events():
    """測試有效簽章（例如 LINE 後台的 Verify 按鈕空事件驗證）"""
    secret = handler.parser.signature_validator.channel_secret.decode("utf-8")
    body = '{"destination":"U1234567890abcdef1234567890abcdef","events":[]}'
    signature = create_signature(secret, body)

    response = client.post(
        "/callback",
        headers={"X-Line-Signature": signature},
        content=body
    )
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
