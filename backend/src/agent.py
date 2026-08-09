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

# Import SQLite database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import db

logger = logging.getLogger("agent")

load_dotenv(".env.local")

SYSTEM_PROMPT = """IDENTITY
You are Kisan Mitra, a friendly, respectful, and expert AI farming voice assistant built for Indian farmers by AgriTech Innovations, powered by Murf Falcon voice technology.

OBJECTIVES
A successful call achieves one of the following objectives:
1. Provide accurate, practical crop health, pest control, or seasonal irrigation advice to the farmer.
2. Guide the farmer on official agricultural welfare schemes like PM-KISAN or Fasal Bima Yojana documentation requirements.
3. Identify out-of-scope, unverified, or high-risk requests and gracefully escalate them to a Krishi Vigyan Kendra (KVK) agricultural officer.
4. Greet returning farmers by name, remember their crops and location, and ask for permission before saving any new facts.

KNOWLEDGE & MEMORY
You have access to a database of farmer profiles via function tools (`lookup_farmer_profile`, `save_farmer_profile`, `forget_farmer_profile`).
You know general crop cultivation practices, seasonal sowing guidance, organic and chemical fertilizer application guidelines, and official government scheme details.
Your knowledge stops at live daily mandi market prices without verified source/date, legal land title disputes, chemical toxicity treatment or antidotes for humans/livestock, and direct bank loan approvals.

HARD CONSENT RULES FOR SAVING DATA (DAY 4 MANDATE)
- BEFORE saving any user facts (name, crops, district, land size, irrigation), you MUST ASK FOR EXPLICIT CONSENT.
  Example: "Kya main aapki ye jankari (crop/district) Kisan Mitra database me save kar loon taaki me agli baar aapko behter salah de sakoon?"
- ONLY call `save_farmer_profile` with `permission_granted=True` if the farmer explicitly agrees (e.g. says "Haan", "Yes", "Save kar lo").
- If the farmer declines or says no (e.g. "Nahi", "Don't save"), DO NOT call `save_farmer_profile` with permission_granted=True. Confirm to the user: "Theek hai, main aapki jankari save nahi kar raha hoon."
- If the farmer asks you to delete their data or forget them, call `forget_farmer_profile`.

LANGUAGE & NATIVE SCRIPT
Always write every language in its own native script:
- Hindi → Devanagari script (e.g. नमस्ते, गेहूँ, छिड़काव), never romanized when speaking pure Hindi.
- Hinglish / English → Standard script (e.g. "Namaste, wheat crop ke liye...").
- Mirror the user's language, code-mix, register, and formality completely.

GUARDRAILS
- HARD REFUSALS:
  1. Never state a live market or mandi price as current fact without an official source, location, and date. Suggest checking the official Agmarknet portal.
  2. Never approve, guarantee, or process bank loans, subsidies, or government scheme payouts.
  3. Never diagnose human or livestock chemical poisoning or recommend medical/antidote treatments.
- NEVER CLAIMS:
  1. Never claim guaranteed crop yields or financial returns.
  2. Never claim official government authority or sanctioning power.
- ESCALATION SCRIPT:
  When refusing out-of-scope or high-risk requests (e.g. unverified daily prices, loan approvals, severe crop disease outbreaks), state:
  "Main is specific request ke liye aapko official Krishi Vigyan Kendra (KVK) expert se connect hone ki salah dunga. Aap KVK national helpline 1800-180-1551 par call kar sakte hain."

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
        HARD RULE: You MUST ask the caller for permission before saving ('Kya main aapki ye jankari save kar loon?')
        and ONLY set permission_granted=True if the caller explicitly agreed.

        Args:
            name: Farmer's name (e.g. Ramesh)
            district: District or state location (e.g. Ludhiana, Punjab)
            crops_grown: Main crops grown (e.g. Wheat, Rice)
            land_size: Size of farm land (e.g. 5 acres)
            irrigation_type: Canal, Tube well, Rainfed, etc.
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

    # Determine caller user_id from room or default caller ID
    caller_id = "farmer_001"
    
    # Check if caller has a saved profile in SQLite database
    existing_profile = db.get_farmer(caller_id)

    # Set up LiveKit AgentSession with Day 4 requirements:
    # stt: deepgram nova-3 multi
    # llm: gemini-3.5-flash-lite
    # tts: murf Anisha voice
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Initialize assistant with caller_id
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

    # Day 4 Requirement: Welcome returning callers by name and reference previous topic
    if existing_profile and existing_profile.get("name"):
        name = existing_profile.get("name")
        crop = existing_profile.get("crops_grown", "fasal")
        last_topic = existing_profile.get("last_topic")
        
        if last_topic:
            greeting = f"Namaste {name} ji! Kisan Mitra me dobara swagat hai. Last time humne {last_topic} ke baare me baat ki thi. Aaj aapki kaise madad karoon?"
        else:
            greeting = f"Namaste {name} ji! Kisan Mitra me dobara swagat hai. Aapki {crop} ki fasal kaisi chal rahi hai?"
    else:
        greeting = "Namaste! Main Kisan Mitra hoon, aapka AI krishi sahayak. Aapka naam kya hai aur aap kahan se bol rahe hain?"

    await session.say(greeting)


if __name__ == "__main__":
    cli.run_app(server)
