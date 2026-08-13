import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Import SQLite database module and Day-5 real-data tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import db
from src.tools import fetch_weather, fetch_market_price, create_escalation_request

logger = logging.getLogger("agent")

load_dotenv(".env.local")

SYSTEM_PROMPT = """IDENTITY
You are Kisan Mitra, a friendly, respectful, and expert AI farming voice assistant built for Tamil Nadu farmers by AgriTech Innovations, powered by Murf Falcon voice technology.

OBJECTIVES
A successful call achieves one of the following objectives:
1. Provide accurate, practical crop health, pest control, seasonal irrigation, spray timing, and harvest advice to Tamil farmers using real weather data.
2. Give verified, up-to-date mandi market prices for crops so farmers can make informed selling decisions.
3. Guide the farmer on official agricultural welfare schemes like PM-KISAN, Kalaignar Centenary Scheme, or Fasal Bima Yojana documentation requirements.
4. Identify out-of-scope or high-risk requests and gracefully escalate them to a Krishi Vigyan Kendra (KVK) agricultural officer.
5. Greet returning farmers by name in Tamil / Tanglish, remember their crops and district, and ask for permission before saving any new facts.

KNOWLEDGE & MEMORY
You have access to the following function tools:
- `lookup_farmer_profile`, `save_farmer_profile`, `forget_farmer_profile` — farmer profile database
- `get_weather_forecast` — fetches a REAL 3-day weather forecast for any Tamil Nadu district from Open-Meteo (IMD data). Use this whenever a farmer asks about rain, weather, spray timing, or harvest timing.
- `get_crop_market_price` — fetches LIVE mandi prices from data.gov.in Agmarknet (official government source). Use this whenever a farmer asks about selling price, market rate, or mandi daam.
- `create_escalation` — creates a human escalation request when a situation exceeds your capability. See ESCALATION TRIGGERS below.
- `hand_off_to_crop_doctor` — HANDOFF TOOL (Day 9): Hands off the caller to our Specialist Agent (Crop Doctor) for crop disease diagnosis, yellowing leaves, pest attacks, or spray recipes.

SPECIALIST AGENT HANDOFF (DAY 9 MANDATE):
- When a farmer asks about crop diseases, yellowing leaves, black spots, pest infestations (stem borer, whiteflies, aphids), or specific spray treatments, YOU MUST HAND OFF to the Crop Specialist using `hand_off_to_crop_doctor`.
- BEFORE calling `hand_off_to_crop_doctor`, tell the farmer in Tamil script:
  "நான் உங்களை எங்கள் பயிர் நோய் மற்றும் பூச்சி வல்லுநரிடம் (Crop Specialist) இணைக்கிறேன்." ("I am connecting you to our crop disease & pest specialist.")

IMPORTANT: When you use `get_weather_forecast` or `get_crop_market_price`, always cite the source and date in your spoken reply. Never invent prices or weather — always call the tool first.

You know general crop cultivation practices (Paddy/Nel, Sugarcane/Karumbu, Cotton, Groundnut/Verkadalai, Banana/Vazhai), seasonal sowing guidance, organic and chemical fertilizer application guidelines, and official government scheme details.
Your knowledge stops at legal land title disputes, chemical toxicity treatment or antidotes for humans/livestock, and direct bank loan approvals.

HARD CONSENT RULES FOR SAVING DATA (DAY 4 MANDATE)
- BEFORE saving any user facts (name, crops, district, land size, irrigation), you MUST ASK FOR EXPLICIT CONSENT in Tamil script.
  Example: "உங்கள் விவரங்களை (பயிர்/மாவட்டம்) Kisan Mitra database-ல் சேமிக்கலாமா? அடுத்த தடவை உதவி எளிதாக இருக்கும்."
- ONLY call `save_farmer_profile` with `permission_granted=True` if the farmer explicitly agrees (e.g. says "ஆமா", "Yes", "சேமிங்க").
- If the farmer declines (e.g. "இல்லை", "No", "வேண்டாம்"), DO NOT save. Confirm: "சரி ஐயா, உங்கள் விவரங்களை சேமிக்கவில்லை."
- If the farmer asks you to delete their data or forget them, call `forget_farmer_profile`.

LANGUAGE & NATIVE SCRIPT
================
CRITICAL — READ THIS FIRST. The TTS voice is a native Tamil speaker (Murf Venkat, ta-IN locale).
For the voice to sound authentic Tamil, you MUST output every Tamil word in Tamil Unicode script.
NEVER romanize Tamil. The following rules are ABSOLUTE and override all other instructions:

RULE 1 — TAMIL SCRIPT IS MANDATORY
  Whenever you speak Tamil or mix Tamil words into a sentence, EVERY Tamil word MUST be written
  in Tamil Unicode script (தமிழ் எழுத்து). This includes:
  - Greetings: வணக்கம் (NOT "Vanakkam")
  - Crops: நெல் (NOT "nel"), கரும்பு (NOT "karumbu"), வாழை (NOT "vazhai")
  - Agriculture: பயிர் (NOT "payir"), உரம் (NOT "uram"), நீர்ப்பாசனம் (NOT "nirpaasanam")
  - Common words: ஆமா (NOT "Aama"), இல்லை (NOT "Illa"), ஐயா (NOT "ayya")
  - Confirmation: சரி (NOT "Seri"), நன்றி (NOT "Nandri")

RULE 2 — TANGLISH IS FORBIDDEN FOR VOICE OUTPUT
  NEVER output romanized Tamil (Tanglish) like: "Vanakkam ayya", "paddy crop ku", "Seri ayya".
  These will be spoken with an English accent by the TTS. Use Tamil Unicode instead.

RULE 3 — ENGLISH-ONLY WORDS STAY IN ROMAN
  Pure English technical terms with no Tamil equivalent may stay in Roman script:
  e.g. "spray", "fertilizer", "PM-KISAN", "KVK", specific chemical names.

RULE 4 — CODE-MIXING PATTERN
  When mixing Tamil and English in one sentence, write Tamil parts in Unicode and English parts in Roman:
  CORRECT: "உங்கள் நெல் பயிருக்கு zinc spray பண்ணலாம்."
  WRONG:   "Unga nel payiru ku zinc spray pannalam."

RULE 5 — MIRROR THE USER'S LANGUAGE
  If the user speaks only English, reply in English (Roman script).
  If the user speaks Tamil or code-mixes Tamil+English, reply using Rules 1-4.


GUARDRAILS
- HARD REFUSALS:
  1. For market prices: ALWAYS use `get_crop_market_price` tool to get official data. Never guess a price. If the tool returns no data, suggest agmarknet.gov.in.
  2. For weather questions: ALWAYS use `get_weather_forecast` tool. Never guess weather.
  3. Never approve, guarantee, or process bank loans, subsidies, or government scheme payouts.
  4. Never diagnose human or livestock chemical poisoning or recommend medical/antidote treatments.
- NEVER CLAIMS:
  1. Never claim guaranteed crop yields or financial returns.
  2. Never claim official government authority or sanctioning power.
- ESCALATION TRIGGERS (Day 7):
  You MUST call `create_escalation` when ANY of these two situations occur:

  TRIGGER 1 — SERIOUS CROP EMERGENCY:
  The farmer reports widespread, sudden, or uncontrolled crop damage:
  examples — "half my field is dead", "all plants wilting overnight", "I see insects everywhere", "unknown black powder on all leaves", "locust attack", "80% crop loss".
  These require a KVK expert immediately. Do NOT try to diagnose or prescribe chemicals.

  TRIGGER 2 — MARKET DATA UNAVAILABLE + URGENT SELLING DECISION:
  You called `get_crop_market_price` and it returned no data, AND the farmer says they need to sell today or urgently need the price for an immediate decision. Do NOT guess a price.

- ESCALATION CONSENT RULE (ABSOLUTE):
  BEFORE calling `create_escalation`, you MUST tell the farmer what information you want to share and ask for their permission.
  Ask in Tamil script: "உங்கள் பெயர், மாவட்டம், மற்றும் பயிர் விவரங்களை ஒரு KVK expert-கு share பண்ணலாமா? (May I share your name, district, and crop details with a KVK expert?)"
  Only call `create_escalation` with `permission_granted=True` if the farmer explicitly agrees.
  If the farmer says no ("இல்லை", "No", "வேண்டாம்"), say: "சரி ஐயா, உங்கள் விவரங்களை share பண்ணவில்லை. KVK helpline 1800-180-1551 ku நீங்களே call பண்ணலாம்." and DO NOT escalate.

- AFTER ESCALATION:
  Read the reference ID to the caller (e.g. 'KM-20260812-0001').
  Explain honestly when a KVK expert will contact them (based on urgency).
  Advise them to call KVK helpline 1800-180-1551 immediately if they cannot wait.

STYLE
- Keep all spoken replies under 20 words per sentence.
- Speak naturally and conversationally for audio/voice output.
- NEVER use markdown formatting, bullet points, numbers, asterisks, brackets, or emojis.
- Be warm, patient, empathetic, and encouraging.
"""


class Assistant(Agent):
    def __init__(self, current_user_id: str = "farmer_001", session_id: str = "") -> None:
        self.current_user_id = current_user_id
        self.session_id = session_id
        # --- Day 8: per-session call tracker (no PII stored) ---
        self._tools_called: List[str] = []
        self._topics_covered: List[str] = []
        self._escalated: bool = False
        self._start_time: datetime = datetime.now()
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_farmer_profile(self, context: RunContext, user_id: str = "") -> str:
        """Looks up a farmer's saved profile in the SQLite database.
        
        Args:
            user_id: Optional caller ID. If empty, uses the active caller's ID.
        """
        uid = user_id.strip() or self.current_user_id
        farmer = db.get_farmer(uid)
        if farmer:
            return (
                f"Saved profile for {farmer.get('name', 'Farmer')}: "
                f"District={farmer.get('district')}, Crops={farmer.get('crops_grown')}, "
                f"LandSize={farmer.get('land_size')}, Irrigation={farmer.get('irrigation_type')}, "
                f"LastTopic={farmer.get('last_topic')}"
            )
        return f"No previous record found for caller ID {uid}."

    @function_tool
    async def save_farmer_profile(
        self,
        context: RunContext,
        name: str = "",
        district: str = "",
        crops_grown: str = "",
        land_size: str = "",
        irrigation_type: str = "",
        last_topic: str = "",
        permission_granted: bool = False
    ) -> str:
        """Saves or updates a farmer's profile in the SQLite database.
        HARD RULE: You MUST ask the caller for permission before saving ('Naan unga details save pannikava?')
        and ONLY set permission_granted=True if the caller explicitly agreed.

        Args:
            name: Farmer's name (e.g. Muthu, Ramesh)
            district: District or state location (e.g. Thanjavur, Madurai)
            crops_grown: Main crops grown (e.g. Paddy/Nel, Sugarcane/Karumbu, Cotton)
            land_size: Size of farm land (e.g. 5 acres)
            irrigation_type: Canal, Borewell, Rainfed, Drip, etc.
            last_topic: Topic or crop query discussed in this call
            permission_granted: Set to True ONLY if the farmer explicitly consented to saving their information.
        """
        if not permission_granted:
            return "ERROR: Permission denied by user. Information was NOT saved to the database."

        farmer = db.save_farmer(
            user_id=self.current_user_id,
            name=name if name else None,
            district=district if district else None,
            crops_grown=crops_grown if crops_grown else None,
            land_size=land_size if land_size else None,
            irrigation_type=irrigation_type if irrigation_type else None,
            last_topic=last_topic if last_topic else None
        )
        return f"SUCCESS: Saved profile for {farmer.get('name', 'Farmer')} in database."

    @function_tool
    async def forget_farmer_profile(self, context: RunContext) -> str:
        """Deletes the caller's profile completely from the database ('Forget me' tool).
        Use this tool when the user asks you to delete their data or forget them.
        """
        deleted = db.delete_farmer(self.current_user_id)
        if deleted:
            return "SUCCESS: All your data has been deleted from Kisan Mitra database."
        return "No existing record was found to delete."

    # ------------------------------------------------------------------
    # DAY 5 — Real-Data Tools
    # ------------------------------------------------------------------

    @function_tool
    async def get_weather_forecast(self, context: RunContext, district: str, days: int = 3) -> str:
        """Fetches a real weather forecast for a Tamil Nadu district from Open-Meteo (IMD data).

        ALWAYS call this tool when the farmer asks about:
        - Will it rain? / Mazhai varuma? / Rain forecast
        - Should I spray today? / Innikku spray panlama?
        - Is it safe to harvest this week?
        - Any question involving weather, temperature, or rainfall.

        Args:
            district: Tamil Nadu district name (e.g. Thanjavur, Madurai, Coimbatore, Chennai)
            days: Number of forecast days (1-7, default 3)
        """
        # Day 8: track tool usage
        self._tools_called.append("get_weather_forecast")
        self._topics_covered.append("weather")

        result = await fetch_weather(district=district, days=days)
        return result["summary"]

    @function_tool
    async def get_crop_market_price(self, context: RunContext, crop: str, district: str = "Tamil Nadu") -> str:
        """Fetches live mandi (wholesale market) prices for a crop from data.gov.in Agmarknet.
        This is the OFFICIAL government market price source — always use this instead of guessing.

        ALWAYS call this tool when the farmer asks about:
        - Market price / Mandi daam / Vilai enna?
        - When to sell? / Eppo sell pannanum?
        - Is the price good now? / Price nallaa irukkaa?
        - Any question about current crop selling price.

        Args:
            crop: Crop name in English or Tamil (e.g. paddy, nel, cotton, sugarcane, groundnut, banana, onion)
            district: District or state for price lookup (default: Tamil Nadu)
        """
        # Day 8: track tool usage
        self._tools_called.append("get_crop_market_price")
        self._topics_covered.append("price")

        result = await fetch_market_price(crop=crop, state="Tamil Nadu")
        return result["summary"]

    # ------------------------------------------------------------------
    # DAY 7 — Human Escalation Tool
    # ------------------------------------------------------------------

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        trigger_type: str,
        situation_summary: str,
        already_checked: str = "",
        urgency: str = "medium",
        contact_method: str = "phone",
        permission_granted: bool = False,
    ) -> str:
        """Creates a human escalation request to a KVK agricultural expert.

        ABSOLUTE RULE: You MUST ask the farmer for permission before calling this tool.
        Ask: 'உங்கள் பெயர், மாவட்டம், மற்றும் பயிர் விவரங்களை ஒரு KVK expert-கு share பண்ணலாமா?'
        ONLY set permission_granted=True if the farmer explicitly agrees.
        If they decline, DO NOT call this tool.

        Call this tool ONLY for these two triggers:
          TRIGGER 1: Serious crop emergency — widespread wilting, mass plant death, locust attacks,
                     uncontrolled pest/disease outbreak the agent cannot diagnose or treat.
          TRIGGER 2: Market data unavailable — `get_crop_market_price` returned no data AND
                     the farmer urgently needs a price for an immediate selling decision.

        Args:
            trigger_type: Must be 'crop_emergency' or 'market_data_missing'
            situation_summary: Concise description of what the farmer reported (no passwords/OTPs/PINs)
            already_checked: What you (the agent) already tried before escalating (e.g. tools used, data checked)
            urgency: 'low' | 'medium' | 'high' | 'emergency'
            contact_method: How the farmer prefers to be contacted — 'phone' | 'whatsapp' | 'none'
            permission_granted: Set to True ONLY if the farmer explicitly gave consent to share their details
        """
        if not permission_granted:
            return (
                "ERROR: The farmer did not give permission to share their information. "
                "Do NOT create an escalation. Advise them to call KVK helpline 1800-180-1551 directly."
            )

        # Resolve farmer details from profile (already consented at sign-up time)
        farmer = db.get_farmer(self.current_user_id) or {}
        farmer_name = farmer.get("name") or "Unknown"
        language = farmer.get("language_preference") or "Tamil"

        result = await create_escalation_request(
            farmer_id=self.current_user_id,
            farmer_name=farmer_name,
            trigger_type=trigger_type,
            situation_summary=situation_summary,
            already_checked=already_checked,
            urgency=urgency,
            language=language,
            contact_method=contact_method,
        )

        if not result.get("success"):
            return result.get("message", "Escalation failed. Please call KVK helpline 1800-180-1551.")

        # Day 8: track escalation
        self._escalated = True
        self._topics_covered.append("escalation")
        self._tools_called.append("create_escalation")

        ref = result["reference_id"]
        return (
            f"Escalation created successfully. Reference ID: {ref}. "
            f"{result['message']}"
        )

    # ------------------------------------------------------------------
    # DAY 9 — Specialist Agent Handoff Tool
    # ------------------------------------------------------------------

    @function_tool
    async def hand_off_to_crop_doctor(self, context: RunContext, disease_or_pest_query: str = "") -> str:
        """Hands off the caller to the Specialist Agent: Crop Doctor (Pest & Crop Disease Specialist).

        ALWAYS call this tool when the farmer asks about:
        - Crop disease diagnosis (yellow leaves, black spots, wilting, leaf curl, root rot, fungal infections)
        - Pest infestations (locusts, stem borer, bollworm, aphids, whiteflies, mealybugs)
        - Specific pesticide, fungicide, or organic spray recommendations (Neem oil, Panchagavya, chemical dosage)
        - Plant health diagnosis requiring specialist attention.

        BEFORE calling this tool, say to the farmer in Tamil script:
        "நான் உங்களை எங்கள் பயிர் நோய் மற்றும் பூச்சி வல்லுநரிடம் (Crop Specialist) இணைக்கிறேன்."

        Args:
            disease_or_pest_query: Summary of the crop disease or pest issue reported by the farmer.
        """
        self._tools_called.append("hand_off_to_crop_doctor")
        self._topics_covered.append("pest_disease_specialist_handoff")

        specialist = CropDoctorAgent(
            current_user_id=self.current_user_id,
            session_id=self.session_id,
            disease_query=disease_or_pest_query
        )
        context.session.update_agent(specialist)
        return (
            f"HANDOFF_SUCCESS: Transferred caller to CropDoctorAgent (Pest & Disease Specialist). "
            f"Query context: '{disease_or_pest_query}'."
        )


# ----------------------------------------------------------------------
# DAY 9 — Specialist Agent Class (Pest & Crop Disease Specialist)
# ----------------------------------------------------------------------

CROP_DOCTOR_PROMPT = """IDENTITY
You are Crop Doctor (பயிர் மருத்துவ வல்லுநர்), a specialized AI crop disease, pest control, and plant health expert for Tamil Nadu farmers, powered by Murf Falcon voice technology.

OBJECTIVES & ROLE
1. Diagnose crop diseases (yellowing leaves, black spots, fungal wilting, leaf curl, root rot) and pest infestations (stem borer, whiteflies, locusts, aphids, bollworm) for Tamil Nadu crops (Paddy/Nel, Sugarcane, Cotton, Groundnut, Banana, Vegetables).
2. Provide practical, step-by-step organic spray recipes (Neem oil, Panchagavya, Agni Astra) or approved chemical treatment guidelines (Zinc sulfate, Carbendazim, Copper oxychloride).
3. Upon taking over the conversation, introduce yourself warmly in Tamil script:
   "வணக்கம்! நான் Kisan Mitra பயிர் மருத்துவ வல்லுநர் (Crop Specialist). உங்கள் பயிர் பிரச்சனையை சொல்லுங்கள், நான் தீர்வு சொல்கிறேன்."
4. Always write Tamil words in pure Tamil Unicode script (e.g. வணக்கம், மஞ்சள் நோய், உரம்). Never use Tanglish.

HANDOFF & HANDBACK RULES:
1. If the farmer asks about general weather, rain forecast, daily mandi market prices, government welfare schemes (PM-KISAN), or deleting their profile, use `hand_back_to_main_agent` to return control to the main Kisan Mitra agent.
2. BEFORE calling `hand_back_to_main_agent`, say: "நான் உங்களை மீண்டும் பிரதான Kisan Mitra உதவியாளரிடம் இணைக்கிறேன்."
3. If crop damage is catastrophic/severe (e.g. 80% loss, complete field death), ask for consent and use `create_escalation` to connect to a human KVK expert.

STYLE
- Keep spoken replies under 20 words per sentence.
- Speak naturally and conversationally.
- NEVER use markdown, bullet points, asterisks, brackets, or emojis.
- Be authoritative, empathetic, precise, and encouraging.
"""


class CropDoctorAgent(Agent):
    """Day 9 Specialist Agent: Crop Disease & Pest Specialist."""

    def __init__(self, current_user_id: str = "farmer_001", session_id: str = "", disease_query: str = "") -> None:
        self.current_user_id = current_user_id
        self.session_id = session_id
        self.disease_query = disease_query
        self._tools_called: List[str] = []
        self._topics_covered: List[str] = ["crop_doctor_specialist"]
        self._escalated: bool = False
        self._start_time: datetime = datetime.now()

        instructions = CROP_DOCTOR_PROMPT
        if disease_query:
            instructions += f"\n\nINITIAL FARMER QUERY TRANSFERRED FROM MAIN AGENT: '{disease_query}'"

        # Inject saved profile data so specialist knows caller context without re-asking
        farmer = db.get_farmer(current_user_id) or {}
        if farmer:
            instructions += (
                f"\n\nFARMER PROFILE CONTEXT: Name={farmer.get('name')}, "
                f"District={farmer.get('district')}, Crops={farmer.get('crops_grown')}, "
                f"Land={farmer.get('land_size')}"
            )

        super().__init__(instructions=instructions)

    @function_tool
    async def get_weather_forecast(self, context: RunContext, district: str, days: int = 3) -> str:
        """Fetches a weather forecast to check if it is safe to spray pesticides or fungicides."""
        self._tools_called.append("get_weather_forecast")
        result = await fetch_weather(district=district, days=days)
        return result["summary"]

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        trigger_type: str,
        situation_summary: str,
        already_checked: str = "",
        urgency: str = "high",
        contact_method: str = "phone",
        permission_granted: bool = False,
    ) -> str:
        """Creates a human escalation request to a KVK agricultural expert for catastrophic crop emergencies."""
        if not permission_granted:
            return "ERROR: Permission denied by farmer. Advise calling KVK 1800-180-1551 directly."

        farmer = db.get_farmer(self.current_user_id) or {}
        result = await create_escalation_request(
            farmer_id=self.current_user_id,
            farmer_name=farmer.get("name") or "Unknown",
            trigger_type=trigger_type,
            situation_summary=situation_summary,
            already_checked=already_checked,
            urgency=urgency,
            language=farmer.get("language_preference") or "Tamil",
            contact_method=contact_method,
        )
        if not result.get("success"):
            return result.get("message", "Escalation failed.")

        self._escalated = True
        self._tools_called.append("create_escalation")
        return f"Escalation created successfully. Reference ID: {result['reference_id']}. {result['message']}"

    @function_tool
    async def hand_back_to_main_agent(self, context: RunContext, reason: str = "") -> str:
        """Hands the caller back to the main Kisan Mitra agent when crop disease/pest query is complete
        or when the farmer asks about non-disease topics (weather, market price, profile memory, schemes).

        BEFORE calling this tool, say:
        "நான் உங்களை மீண்டும் பிரதான Kisan Mitra உதவியாளரிடம் இணைக்கிறேன்."

        Args:
            reason: Reason for handing back (e.g. 'Farmer asked for weather forecast', 'Disease advice complete')
        """
        self._tools_called.append("hand_back_to_main_agent")
        self._topics_covered.append("handback_to_main_agent")

        main_agent = Assistant(
            current_user_id=self.current_user_id,
            session_id=self.session_id
        )
        context.session.update_agent(main_agent)
        return "HANDOFF_SUCCESS: Switched back to main Kisan Mitra agent."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    caller_id = "farmer_001"
    existing_profile = db.get_farmer(caller_id)

    # Day 8: Determine channel (SIP vs browser)
    session_id = ctx.room.name or f"session_{int(datetime.now().timestamp())}"
    channel = "sip" if any(
        p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
        for p in ctx.room.remote_participants.values()
    ) else "browser"

    # Day 8: Create call log at session start
    db.create_call_log(
        session_id=session_id,
        caller_id=caller_id,
        channel=channel,
        language="Tamil",
    )
    logger.info(f"Call log created for session={session_id} channel={channel}")

    # Set up LiveKit AgentSession with Tamil/Tanglish + Murf Venkat voice
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="Anisha",   # Murf Falcon multilingual voice
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    assistant = Assistant(current_user_id=caller_id, session_id=session_id)

    # Day 8: Hook into session/room close to record call outcome
    @ctx.room.on("disconnected")
    def _on_room_disconnected(*args):
        """Finalise the call log when the room closes."""
        duration = int((datetime.now() - assistant._start_time).total_seconds())
        tools = list(dict.fromkeys(assistant._tools_called))   # deduplicated, ordered
        topics = list(dict.fromkeys(assistant._topics_covered))

        # Determine outcome
        if duration < 10:
            outcome = "failed"
            failure_type = "early_hangup"
        elif tools:
            # At least one tool was called successfully
            outcome = "success"
            failure_type = "none"
        elif duration >= 30:
            # Long call but no tools — gave conversational advice
            outcome = "success"
            failure_type = "none"
        else:
            outcome = "failed"
            failure_type = "no_tool_called"

        try:
            db.update_call_log(
                session_id=session_id,
                outcome=outcome,
                failure_type=failure_type,
                topics_discussed=",".join(topics),
                tools_called=",".join(tools),
                escalated=assistant._escalated,
            )
            logger.info(f"Call log finalised: session={session_id} outcome={outcome} duration={duration}s")
        except Exception as e:
            logger.error(f"Failed to finalise call log for {session_id}: {e}")

    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await ctx.connect()

    # Returning caller greeting in Tamil Unicode script (not Tanglish — avoids English accent)
    if existing_profile and existing_profile.get("name"):
        name = existing_profile.get("name")
        crop = existing_profile.get("crops_grown", "பயிர்")
        last_topic = existing_profile.get("last_topic")

        if last_topic:
            greeting = f"வணக்கம் {name} ஐயா! Kisan Mitra-க்கு மீண்டும் வாருங்கள். கடைசியாக {last_topic} பற்றி பேசினோம். இன்று என்ன உதவி வேண்டும்?"
        else:
            greeting = f"வணக்கம் {name} ஐயா! Kisan Mitra-க்கு மீண்டும் வாருங்கள். உங்கள் {crop} பயிர் எப்படி இருக்கிறது?"
    else:
        greeting = "வணக்கம்! நான் Kisan Mitra, உங்கள் AI விவசாய உதவியாளர். உங்கள் பெயர் என்ன, எந்த மாவட்டம்?"

    await session.say(greeting)


if __name__ == "__main__":
    cli.run_app(server)
