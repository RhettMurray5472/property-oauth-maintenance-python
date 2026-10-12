import os

import pytest

from src.property_service import InfraiClient, InfraiError, MaintenanceRequest, accept_maintenance_request


class FakeClient:
    def __init__(self, accepted: bool):
        self.accepted = accepted

    def verify_captcha(self, widget_record_id: str, token: str, action: str):
        if not self.accepted:
            raise InfraiError("CAPTCHA_REJECTED", {"message": "rejected"}, 422)
        return {"ok": True, "data": {"verified": True}}


def test_accepted_captcha_creates_property_work_item():
    request = MaintenanceRequest("building-7", "tenant-3", "Leaking sink", "token", "widget-1")
    result = accept_maintenance_request(FakeClient(True), request)
    assert result == {"status": "accepted", "property_id": "building-7", "tenant_id": "tenant-3", "issue": "Leaking sink"}


def test_rejected_captcha_does_not_accept_request():
    request = MaintenanceRequest("building-7", "tenant-3", "Leaking sink", "token", "widget-1")
    with pytest.raises(InfraiError):
        accept_maintenance_request(FakeClient(False), request)


def test_verify_captcha_sends_required_widget_id(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    client = InfraiClient()
    sent = {}

    def request(method, path, body):
        sent.update(body)
        return {"ok": True}

    monkeypatch.setattr(client, "request", request)
    client.verify_captcha("widget-1", "token", "maintenance_request")
    assert sent["widget_record_id"] == "widget-1"
    assert sent["token"] == "token"
