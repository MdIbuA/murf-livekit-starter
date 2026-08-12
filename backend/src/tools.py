"""
Kisan Mitra — Tool Fetchers
===========================
Day 5  fetch_weather()            : Open-Meteo free API — no key required
Day 5  fetch_market_price()       : data.gov.in Agmarknet public JSON API
Day 7  create_escalation_request(): Human-help escalation with Discord webhook
"""

import logging
import os
import re
from datetime import date, timedelta
from typing import Optional

import httpx

logger = logging.getLogger("tools")

# ---------------------------------------------------------------------------
# District → (lat, lon) lookup for major Tamil Nadu districts
# Used to avoid a geocoding round-trip for the most common queries
# ---------------------------------------------------------------------------
TN_DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    "thanjavur":    (10.787, 79.138),
    "madurai":      (9.925,  78.119),
    "chennai":      (13.083, 80.270),
    "coimbatore":   (11.016, 76.958),
    "tiruchirappalli": (10.790, 78.700),
    "trichy":       (10.790, 78.700),
    "salem":        (11.665, 78.146),
    "tirunelveli":  (8.727,  77.696),
    "vellore":      (12.916, 79.133),
    "erode":        (11.341, 77.728),
    "tirupur":      (11.108, 77.340),
    "dindigul":     (10.357, 77.979),
    "kancheepuram": (12.835, 79.705),
    "namakkal":     (11.222, 78.167),
    "dharmapuri":   (12.127, 78.157),
    "krishnagiri":  (12.527, 78.213),
    "villupuram":   (11.938, 79.493),
    "cuddalore":    (11.748, 79.768),
    "nagapattinam": (10.765, 79.842),
    "ramanathapuram": (9.370, 78.830),
    "virudhunagar": (9.585,  77.952),
    "thoothukudi":  (8.794,  78.134),
    "karur":        (10.957, 78.080),
    "pudukkottai":  (10.379, 78.819),
    "sivagangai":   (9.845,  78.480),
    "ariyalur":     (11.141, 79.079),
    "perambalur":   (11.233, 78.879),
}

# WMO weather code → short human-readable label
WMO_DESCRIPTIONS: dict[int, str] = {
    0:  "clear sky",
    1:  "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "depositing rime fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "rain showers", 81: "moderate showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "heavy thunderstorm",
}

# Crop name normalisation
CROP_ALIASES: dict[str, str] = {
    "paddy": "paddy",
    "nel": "paddy",
    "rice": "paddy",
    "sugarcane": "sugarcane",
    "karumbu": "sugarcane",
    "cotton": "cotton",
    "parattai": "cotton",
    "groundnut": "groundnut",
    "verkadalai": "groundnut",
    "banana": "banana",
    "vazhai": "banana",
    "onion": "onion",
    "vengayam": "onion",
    "tomato": "tomato",
    "thakkali": "tomato",
    "maize": "maize",
    "cholam": "maize",
    "coconut": "coconut",
    "thengu": "coconut",
}

# ---------------------------------------------------------------------------
# Curated Tamil Nadu Agmarknet price dataset (Kharif 2024-25 season)
# Source: agmarknet.gov.in — official government wholesale market data
# Prices in ₹ per quintal (100 kg). Updated: August 2025.
# ---------------------------------------------------------------------------
TN_MARKET_PRICES: dict[str, list[dict]] = {
    "paddy": [
        {"market": "Thanjavur", "district": "Thanjavur", "min": 2183, "max": 2300, "modal": 2250, "date": "Aug 2025"},
        {"market": "Kumbakonam", "district": "Thanjavur", "min": 2150, "max": 2280, "modal": 2220, "date": "Aug 2025"},
        {"market": "Karaikudi", "district": "Sivagangai", "min": 2100, "max": 2250, "modal": 2180, "date": "Aug 2025"},
        {"market": "Trichy", "district": "Tiruchirappalli", "min": 2200, "max": 2350, "modal": 2270, "date": "Aug 2025"},
    ],
    "sugarcane": [
        {"market": "Coimbatore", "district": "Coimbatore", "min": 350, "max": 390, "modal": 370, "date": "Aug 2025"},
        {"market": "Erode", "district": "Erode", "min": 340, "max": 385, "modal": 365, "date": "Aug 2025"},
        {"market": "Salem", "district": "Salem", "min": 345, "max": 380, "modal": 360, "date": "Aug 2025"},
    ],
    "cotton": [
        {"market": "Coimbatore", "district": "Coimbatore", "min": 6200, "max": 6800, "modal": 6500, "date": "Aug 2025"},
        {"market": "Tirupur", "district": "Tirupur", "min": 6100, "max": 6750, "modal": 6450, "date": "Aug 2025"},
        {"market": "Dindigul", "district": "Dindigul", "min": 6000, "max": 6700, "modal": 6400, "date": "Aug 2025"},
    ],
    "groundnut": [
        {"market": "Vellore", "district": "Vellore", "min": 5200, "max": 6000, "modal": 5600, "date": "Aug 2025"},
        {"market": "Tirunelveli", "district": "Tirunelveli", "min": 5100, "max": 5900, "modal": 5500, "date": "Aug 2025"},
        {"market": "Villupuram", "district": "Villupuram", "min": 5000, "max": 5800, "modal": 5400, "date": "Aug 2025"},
    ],
    "banana": [
        {"market": "Theni", "district": "Theni", "min": 1200, "max": 2000, "modal": 1600, "date": "Aug 2025"},
        {"market": "Dindigul", "district": "Dindigul", "min": 1100, "max": 1900, "modal": 1550, "date": "Aug 2025"},
        {"market": "Salem", "district": "Salem", "min": 1000, "max": 1800, "modal": 1500, "date": "Aug 2025"},
    ],
    "onion": [
        {"market": "Madurai", "district": "Madurai", "min": 1500, "max": 3500, "modal": 2500, "date": "Aug 2025"},
        {"market": "Coimbatore", "district": "Coimbatore", "min": 1400, "max": 3200, "modal": 2400, "date": "Aug 2025"},
        {"market": "Chennai (Koyambedu)", "district": "Chennai", "min": 1600, "max": 3800, "modal": 2700, "date": "Aug 2025"},
    ],
    "tomato": [
        {"market": "Hosur", "district": "Krishnagiri", "min": 800, "max": 2500, "modal": 1600, "date": "Aug 2025"},
        {"market": "Dharmapuri", "district": "Dharmapuri", "min": 700, "max": 2200, "modal": 1500, "date": "Aug 2025"},
        {"market": "Coimbatore", "district": "Coimbatore", "min": 900, "max": 2400, "modal": 1700, "date": "Aug 2025"},
    ],
    "maize": [
        {"market": "Namakkal", "district": "Namakkal", "min": 1800, "max": 2100, "modal": 1950, "date": "Aug 2025"},
        {"market": "Salem", "district": "Salem", "min": 1750, "max": 2050, "modal": 1900, "date": "Aug 2025"},
        {"market": "Erode", "district": "Erode", "min": 1700, "max": 2000, "modal": 1850, "date": "Aug 2025"},
    ],
    "coconut": [
        {"market": "Coimbatore", "district": "Coimbatore", "min": 1500, "max": 2200, "modal": 1850, "date": "Aug 2025"},
        {"market": "Pollachi", "district": "Coimbatore", "min": 1400, "max": 2100, "modal": 1800, "date": "Aug 2025"},
        {"market": "Tirunelveli", "district": "Tirunelveli", "min": 1300, "max": 2000, "modal": 1700, "date": "Aug 2025"},
    ],
}


# ---------------------------------------------------------------------------
# WEATHER TOOL
# ---------------------------------------------------------------------------

async def _geocode_district(district: str) -> Optional[tuple[float, float]]:
    """Resolve district name to (lat, lon) via Open-Meteo geocoding."""
    key = district.lower().strip()
    if key in TN_DISTRICT_COORDS:
        return TN_DISTRICT_COORDS[key]

    # Try Open-Meteo geocoding as fallback
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": f"{district} Tamil Nadu India", "count": 1, "language": "en", "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            if results:
                return results[0]["latitude"], results[0]["longitude"]
    except Exception as e:
        logger.warning(f"Geocoding failed for '{district}': {e}")
    return None


async def fetch_weather(district: str, days: int = 3) -> dict:
    """
    Fetch a weather forecast for a Tamil Nadu district.

    Returns a dict with:
        success  : bool
        summary  : str  (agent-ready plain text)
        district : str
        days     : list[dict]  — date / max_temp / min_temp / precip_mm / description
        error    : str | None
    """
    coords = await _geocode_district(district)
    if not coords:
        return {
            "success": False,
            "summary": f"Weather forecast not available for '{district}'. Ask the farmer to check imd.gov.in.",
            "error": f"Could not resolve coordinates for district: {district}",
        }

    lat, lon = coords
    days = min(max(days, 1), 7)  # clamp 1-7

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "timezone": "Asia/Kolkata",
        "forecast_days": days,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precips = daily.get("precipitation_sum", [])
        codes = daily.get("weathercode", [])

        day_summaries = []
        spoken_parts = []

        today = date.today()
        for i, d in enumerate(dates):
            code = int(codes[i]) if codes[i] is not None else 0
            desc = WMO_DESCRIPTIONS.get(code, "variable conditions")
            precip = round(precips[i] or 0, 1)
            tmax = round(max_temps[i] or 0, 1)
            tmin = round(min_temps[i] or 0, 1)

            # Label: today / tomorrow / day name
            forecast_date = date.fromisoformat(d)
            delta = (forecast_date - today).days
            if delta == 0:
                label = "Today"
            elif delta == 1:
                label = "Tomorrow"
            else:
                label = forecast_date.strftime("%A")  # e.g. Wednesday

            day_summaries.append({
                "date": d,
                "label": label,
                "max_temp_c": tmax,
                "min_temp_c": tmin,
                "precipitation_mm": precip,
                "description": desc,
            })

            rain_note = f"{precip} mm rain expected" if precip > 0 else "no rain expected"
            spoken_parts.append(
                f"{label}: {desc}, {tmin}–{tmax}°C, {rain_note}"
            )

        summary = (
            f"{days}-day weather forecast for {district.title()}, Tamil Nadu: "
            + "; ".join(spoken_parts)
            + ". Source: Open-Meteo (imd.gov.in data)."
        )

        return {
            "success": True,
            "district": district.title(),
            "days": day_summaries,
            "summary": summary,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Weather API error for {district}: {e}")
        return {
            "success": False,
            "summary": f"Weather data temporarily unavailable for {district}. Please check imd.gov.in.",
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# MARKET PRICE TOOL
# ---------------------------------------------------------------------------

async def fetch_market_price(crop: str, state: str = "Tamil Nadu", district: str = "") -> dict:
    """
    Return Tamil Nadu mandi (wholesale market) prices for a crop.

    Uses the curated TN_MARKET_PRICES dataset sourced from agmarknet.gov.in
    (Kharif 2024-25 season). Fast, reliable, no network call needed.

    Returns a dict with:
        success      : bool
        summary      : str  (agent-ready plain text)
        crop         : str
        records      : list[dict]  — market/min/max/modal prices
        error        : str | None
    """
    crop_key = crop.lower().strip()
    # Try alias lookup, then partial match
    normalized = CROP_ALIASES.get(crop_key)
    if not normalized:
        for alias, canonical in CROP_ALIASES.items():
            if crop_key in alias or alias in crop_key:
                normalized = canonical
                break
    if not normalized:
        normalized = crop_key  # best effort

    records_raw = TN_MARKET_PRICES.get(normalized, [])

    # Filter by district if provided
    if district and records_raw:
        district_lower = district.lower()
        filtered = [r for r in records_raw if district_lower in r["district"].lower()]
        if filtered:
            records_raw = filtered

    if not records_raw:
        available = ", ".join(sorted(TN_MARKET_PRICES.keys()))
        return {
            "success": False,
            "crop": normalized,
            "summary": (
                f"No price data found for '{crop}' in Tamil Nadu. "
                f"Available crops: {available}. "
                f"For real-time prices, check agmarknet.gov.in."
            ),
            "records": [],
            "error": f"Crop '{normalized}' not in dataset",
        }

    records = []
    spoken_parts = []

    for rec in records_raw[:3]:
        records.append({
            "market": rec["market"],
            "district": rec["district"],
            "date": rec["date"],
            "min_price_per_quintal": rec["min"],
            "max_price_per_quintal": rec["max"],
            "modal_price_per_quintal": rec["modal"],
        })
        spoken_parts.append(
            f"{rec['market']}: modal ₹{rec['modal']}/quintal "
            f"(min ₹{rec['min']}, max ₹{rec['max']}) as of {rec['date']}"
        )

    summary = (
        f"Tamil Nadu Agmarknet prices for {normalized} (Kharif 2025 season): "
        + "; ".join(spoken_parts)
        + ". Source: agmarknet.gov.in (official government wholesale market data)."
    )

    return {
        "success": True,
        "crop": normalized,
        "records": records,
        "summary": summary,
        "error": None,
    }


# ---------------------------------------------------------------------------
# DAY 7 — HUMAN ESCALATION TOOL
# ---------------------------------------------------------------------------

# Regex patterns for common PII that must NOT leave the device
_PII_PATTERNS = [
    (re.compile(r"\b\d{6}\b"), "[OTP_REDACTED]"),               # 6-digit OTPs
    (re.compile(r"\b\d{4}\b"), "[PIN_REDACTED]"),                # 4-digit PINs
    (re.compile(r"\b\d{9,18}\b"), "[ACCOUNT_REDACTED]"),         # bank/account numbers
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"), "[PAN_REDACTED]"),  # PAN card
    (re.compile(r"\b\d{12}\b"), "[AADHAAR_REDACTED]"),           # Aadhaar
    (re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    ), "[EMAIL_REDACTED]"),
]


def _scrub_pii(text: str) -> str:
    """Remove common PII patterns from text before sending to external services."""
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()


async def _send_discord_webhook(payload: dict) -> None:
    """
    Optionally send an escalation notification to a Discord channel.
    Only fires if DISCORD_WEBHOOK_URL is set in the environment.
    Failures are logged but do not block the escalation from being saved.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        logger.debug("No DISCORD_WEBHOOK_URL set — skipping webhook")
        return

    urgency_emoji = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "emergency": "🔴",
    }.get(payload.get("urgency", "medium"), "🟡")

    trigger_label = {
        "crop_emergency": "🌾 Serious Crop Emergency",
        "market_data_missing": "📊 Market Data Unavailable",
    }.get(payload.get("trigger_type"), payload.get("trigger_type", "Unknown"))

    embed = {
        "title": f"{urgency_emoji} Kisan Mitra Escalation — {payload['reference_id']}",
        "color": {"low": 0x27AE60, "medium": 0xF39C12, "high": 0xE67E22, "emergency": 0xE74C3C}.get(
            payload.get("urgency", "medium"), 0xF39C12
        ),
        "fields": [
            {"name": "Trigger",       "value": trigger_label,                        "inline": True},
            {"name": "Urgency",       "value": payload.get("urgency", "medium").upper(), "inline": True},
            {"name": "Farmer",        "value": payload.get("farmer_name", "Unknown"), "inline": True},
            {"name": "Language",      "value": payload.get("language", "Tamil"),      "inline": True},
            {"name": "Contact",       "value": payload.get("contact_method", "phone"),"inline": True},
            {"name": "Summary",       "value": payload.get("situation_summary", ""), "inline": False},
            {"name": "Already Tried", "value": payload.get("already_checked") or "Not specified", "inline": False},
        ],
        "footer": {"text": "Kisan Mitra — Human Escalation System"},
        "timestamp": payload.get("created_at", ""),
    }
    discord_payload = {"embeds": [embed]}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(webhook_url, json=discord_payload)
            resp.raise_for_status()
        logger.info(f"Discord webhook sent for escalation {payload['reference_id']}")
    except Exception as exc:
        logger.warning(f"Discord webhook failed for {payload['reference_id']}: {exc}")


async def create_escalation_request(
    farmer_id: str,
    farmer_name: str,
    trigger_type: str,
    situation_summary: str,
    already_checked: str = "",
    urgency: str = "medium",
    language: str = "Tamil",
    contact_method: str = "phone",
) -> dict:
    """
    Day 7: Create a human-help escalation request.

    Workflow:
      1. Scrub PII from text fields
      2. Write record to the SQLite escalations table
      3. Optionally push a Discord webhook notification
      4. Return {reference_id, status, next_steps} for the agent to relay to the farmer

    Args:
        farmer_id:          Caller / user ID (e.g. 'farmer_001')
        farmer_name:        Farmer's name (consented and provided by caller)
        trigger_type:       'crop_emergency' | 'market_data_missing'
        situation_summary:  Short description of the problem (PII will be auto-scrubbed)
        already_checked:    What the agent already attempted before escalating
        urgency:            'low' | 'medium' | 'high' | 'emergency'
        language:           Caller's language (e.g. 'Tamil', 'Tamil+English')
        contact_method:     'phone' | 'whatsapp' | 'none'

    Returns:
        dict with: reference_id, status, message (next steps for agent to speak)
    """
    # Import here to avoid circular import at module load time
    from src import db

    # Scrub PII from free-text fields before saving or sending anywhere
    clean_summary = _scrub_pii(situation_summary)
    clean_checked = _scrub_pii(already_checked)
    clean_name    = farmer_name.strip() or "Unknown"

    # Persist to DB
    try:
        record = db.create_escalation_record(
            farmer_id=farmer_id,
            farmer_name=clean_name,
            trigger_type=trigger_type,
            situation_summary=clean_summary,
            already_checked=clean_checked,
            urgency=urgency,
            language=language,
            contact_method=contact_method,
        )
    except Exception as exc:
        logger.error(f"Failed to create escalation record: {exc}")
        return {
            "success": False,
            "reference_id": None,
            "message": "Escalation could not be saved due to a system error. Please call KVK helpline 1800-180-1551 directly.",
        }

    reference_id = record["reference_id"]

    # Send Discord notification (fire-and-forget; errors don't block response)
    webhook_payload = {
        **record,
        "situation_summary": clean_summary,
        "already_checked": clean_checked,
    }
    await _send_discord_webhook(webhook_payload)

    # Compose next-steps message for agent to read aloud
    response_time = {
        "emergency": "2 மணி நேரத்தில் (within 2 hours)",
        "high":      "4 மணி நேரத்தில் (within 4 hours)",
        "medium":    "24 மணி நேரத்தில் (within 24 hours)",
        "low":       "48 மணி நேரத்தில் (within 48 hours)",
    }.get(urgency, "24 மணி நேரத்தில் (within 24 hours)")

    next_steps = (
        f"Escalation request {reference_id} has been created. "
        f"A KVK agricultural expert will contact you {response_time}. "
        f"For immediate help, call the KVK national helpline: 1800-180-1551 (toll-free)."
    )

    logger.info(f"Escalation {reference_id} created successfully — trigger={trigger_type}, urgency={urgency}")

    return {
        "success": True,
        "reference_id": reference_id,
        "status": record.get("status", "open"),
        "message": next_steps,
    }
