import logging
import os
import sys

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
from src.tools import fetch_weather, fetch_market_price

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
- ESCALATION SCRIPT:
  When refusing out-of-scope or high-risk requests (e.g. loan approvals, severe disease outbreaks, legal disputes), state:
  "Indha specific request kaga naan ungalukku official Krishi Vigyan Kendra (KVK) expert kitta pesalaam nu solren. KVK national helpline 1800-180-1551 ku call pannunga."

STYLE
- Keep all spoken replies under 20 words per sentence.
- Speak naturally and conversationally for audio/voice output.
- NEVER use markdown formatting, bullet points, numbers, asterisks, brackets, or emojis.
- Be warm, patient, empathetic, and encouraging.
"""


class Assistant(Agent):
    def __init__(self, current_user_id: str = "farmer_001") -> None:
        self.current_user_id = current_user_id
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
        result = await fetch_market_price(crop=crop, state="Tamil Nadu")
        return result["summary"]


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

    # Set up LiveKit AgentSession with Tamil/Tanglish + Murf Venkat voice
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="Venkat",   # Native Tamil voice (ta-IN) — gives authentic Tamil accent
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    assistant = Assistant(current_user_id=caller_id)

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
