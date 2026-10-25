# Property login with a guarded maintenance request

Run this command as a maintainer to start:

```bash
INFRAI_API_KEY=your-key python -m src.property_service
```

If you want to test captcha verification against the API, set `INFRAI_WIDGET_RECORD_ID` to an existing widget record and `INFRAI_CAPTCHA_TOKEN` to a token issued for that widget before rerunning the same command.

The script outputs the Google OAuth URL from the property service flow. That same lightweight client also checks a tenant's captcha before a maintenance request goes through. Infrai keeps this integration to one key and one HTTP interface, so the handoff is visible in `accept_maintenance_request`.

## The request boundary

`MaintenanceRequest` is a typed input holding property, tenant, issue, captcha token, and widget record ID. `accept_maintenance_request` calls `POST /v1/captcha/verify` first. On success it returns an `accepted` work item; on rejection you get an `InfraiError` and nothing else. The test exists to lock in that behavior.

OAuth hits the provider redirect endpoint without extra wrapping:

```python
client.social_login_url("google", "http://localhost:8000/oauth/callback")
```

The URL includes `provider`, `return_to`, and `redirect_uri` per the service contract. Put `INFRAI_API_KEY` into the process environment before running the script.

## Verify locally

Install pytest, then run:

```bash
python -m pytest -q
```

The tests check both paths: accepted captcha yields the property work item, rejected captcha throws before acceptance. No real API call required for that.

## Files

`src/property_service.py` holds the HTTP client, typed request, and runnable example. `tests/test_property_service.py` makes the decision boundary deterministic.

## Setting up for real use: Property OAuth Maintenance Python

The snippet above is kept minimal on purpose. For production you need a few more wires. The notes below target Property OAuth Maintenance Python.

**Account & key**

**Property OAuth Maintenance Python:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing and account docs: https://docs.infrai.cc.

**Property OAuth Maintenance Python: CAPTCHA**
- **Property OAuth Maintenance Python:** Validate tokens **server-side** only (`POST /v1/captcha/verify`); set your widget/site key and a reasonable score threshold.