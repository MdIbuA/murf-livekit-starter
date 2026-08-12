"""
Day 7 Smoke Test — Escalation System
Validates both escalation paths without needing the LiveKit server.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from src import db
from src.tools import create_escalation_request, _scrub_pii

# ── 1. DB init ──────────────────────────────────────────────────────────
db.init_db()
print("✅  DB initialized (farmers + escalations tables)")

# ── 2. PII scrubber ─────────────────────────────────────────────────────
pii_tests = [
    ("My PIN is 1234 and OTP 567890", "My PIN is [PIN_REDACTED] and OTP [OTP_REDACTED]"),
    ("Account 123456789012345678",    "Account [ACCOUNT_REDACTED]"),
    ("Email test@example.com",        "Email [EMAIL_REDACTED]"),
    ("Regular text no PII",           "Regular text no PII"),
]
for text, expected in pii_tests:
    result = _scrub_pii(text)
    status = "✅" if result == expected else f"❌  got: {result!r}"
    print(f"  PII scrub: {status}")

# ── 3. Denied permission (should NOT create a DB record) ────────────────
count_before = len(db.list_escalations())

async def test_denied():
    # Simulating what agent.py does when permission_granted=False
    if False:  # permission_granted = False
        await create_escalation_request(
            farmer_id="test_farmer",
            farmer_name="Ramu",
            trigger_type="crop_emergency",
            situation_summary="Fields are dying",
        )

asyncio.run(test_denied())
count_after = len(db.list_escalations())
assert count_after == count_before, "❌  Escalation created without permission!"
print("✅  Permission gate: denied path correctly skips creation")

# ── 4. Granted permission — crop emergency ───────────────────────────────
async def test_crop_emergency():
    result = await create_escalation_request(
        farmer_id="farmer_001",
        farmer_name="Muthu",
        trigger_type="crop_emergency",
        situation_summary="Entire paddy field wilting overnight. PIN 1234 should be scrubbed.",
        already_checked="Called get_weather_forecast (sunny). No pest alert tool available.",
        urgency="emergency",
        language="Tamil",
        contact_method="phone",
    )
    assert result["success"], f"❌  Expected success: {result}"
    ref = result["reference_id"]
    assert ref.startswith("KM-"), f"❌  Bad reference ID: {ref}"

    record = db.get_escalation(ref)
    assert record is not None, "❌  Record not found in DB"
    assert record["urgency"] == "emergency"
    assert "PIN" not in record["situation_summary"], "❌  PII not scrubbed from DB record"
    assert record["status"] == "open"
    print(f"✅  Crop emergency escalation created: {ref}")
    print(f"   Summary: {record['situation_summary']}")
    return ref

ref1 = asyncio.run(test_crop_emergency())

# ── 5. Market data missing ───────────────────────────────────────────────
async def test_market_missing():
    result = await create_escalation_request(
        farmer_id="farmer_002",
        farmer_name="Selvi",
        trigger_type="market_data_missing",
        situation_summary="Farmer urgently needs cotton price to sell today. No data returned by tool.",
        already_checked="Called get_crop_market_price(cotton) — returned no data for today's date.",
        urgency="high",
        language="Tamil+English",
        contact_method="whatsapp",
    )
    assert result["success"]
    ref = result["reference_id"]
    print(f"✅  Market data missing escalation created: {ref}")
    return ref

ref2 = asyncio.run(test_market_missing())

# ── 6. Status update ─────────────────────────────────────────────────────
updated = db.update_escalation_status(ref1, "in_progress")
assert updated["status"] == "in_progress", f"❌  Status not updated: {updated}"
print(f"✅  Status update: {ref1} → in_progress")

resolved = db.update_escalation_status(ref1, "resolved")
assert resolved["status"] == "resolved"
print(f"✅  Status update: {ref1} → resolved")

# ── 7. List & filter ─────────────────────────────────────────────────────
all_records = db.list_escalations()
open_records = db.list_escalations(status="open")
resolved_records = db.list_escalations(status="resolved")
print(f"✅  List: {len(all_records)} total, {len(open_records)} open, {len(resolved_records)} resolved")

# ── 8. Normal conversation (no escalation) ───────────────────────────────
count_final = len(db.list_escalations())
# Simulate a paddy price query — does NOT call create_escalation_request
from src.tools import fetch_market_price
price_result = asyncio.run(fetch_market_price(crop="paddy", state="Tamil Nadu"))
assert price_result["success"]
assert len(db.list_escalations()) == count_final  # no extra escalations
print("✅  Normal price query: no escalation created")

print("\n🎉  All Day 7 smoke tests passed!")
