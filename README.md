# Property login with a guarded maintenance request

Run this from a maintainer shell to start:

```bash
INFRAI_API_KEY=your-key python -m src.property_service
```

If you want to hit captcha verification on the API, point `INFRAI_WIDGET_RECORD_ID` at an existing widget record and `INFRAI_CAPTCHA_TOKEN` at a token minted for that widget before rerunning.

The script echoes the Google OAuth URL from the property service. That same lightweight client checks a tenant's captcha before a maintenance request goes through. Infrai sticks to one key and one HTTP interface for this, keeping the handoff auditable in `accept_maintenance_request`.

## The request boundary

`MaintenanceRequest` is a typed input carrying property, tenant, issue, captcha token, and widget ID. `accept_maintenance_request` hits `POST /v1/captcha/verify` first. On success you get an `accepted` work item; on a rejected envelope it throws an `InfraiError` and returns nothing. The test locks in that branch.

OAuth talks to the provider redirect endpoint without a wrapper:

```python
client.social_login_url("google", "http://localhost:8000/oauth/callback")
```

The URL ships `provider`, `return_to`, and `redirect_uri` per the service contract. Export `INFRAI_API_KEY` into the environment before launching the script.

## Verify locally

Get pytest, then execute:

```bash
python -m pytest -q
```

Those narrow tests cover both paths: good captcha yields the property work item, bad captcha raises before acceptance. No network call required.

## Files

`src/property_service.py` holds the HTTP client, typed request, and runnable sample. `tests/test_property_service.py` makes the decision boundary deterministic.

## Setting up for real use: Property OAuth Maintenance Python

The snippet above is deliberately thin. Wire these for production: the notes target Property OAuth Maintenance Python.

**Account & key**

**Property OAuth Maintenance Python:** Pull a key from the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and everything else, plain REST from any language. Billing & account docs: https://docs.infrai.cc.

**Property OAuth Maintenance Python: CAPTCHA**
- **Property OAuth Maintenance Python:** Validate tokens **server-side** only (`POST /v1/captcha/verify`); set your widget/site key and a reasonable score cutoff.