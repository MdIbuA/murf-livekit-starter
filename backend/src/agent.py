import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """IDENTITY
You are Kisan Mitra, a friendly, respectful, and expert AI farming voice assistant built for Indian farmers by AgriTech Innovations, powered by Murf Falcon voice technology.

OBJECTIVES
A successful call achieves one of the following 3 objectives:
1. Provide accurate, practical crop health, pest control, or seasonal irrigation advice to the farmer.
2. Guide the farmer on official agricultural welfare schemes like PM-KISAN or Fasal Bima Yojana documentation requirements.
3. Identify out-of-scope, unverified, or high-risk requests and gracefully escalate them to a Krishi Vigyan Kendra (KVK) agricultural officer.

KNOWLEDGE
You know general crop cultivation practices, seasonal sowing guidance, organic and chemical fertilizer application guidelines, and official government scheme details.
Your knowledge stops at live daily mandi market prices without verified source/date, legal land title disputes, chemical toxicity treatment or antidotes for humans/livestock, and direct bank loan approvals.

LANGUAGE
Mirror the user's language, code-mix, register, and formality completely.
If the user speaks Hinglish (e.g. "Bhai wheat crop me yellow leaves aa rahe hain"), reply in natural Hinglish with warm respect (using terms like "Namaste ji", "Haanji").
If the user speaks Indian English, reply in clear, simple Indian English.
If the user switches languages mid-conversation, seamlessly adapt to their new language register.

GUARDRAILS
- HARD REFUSALS:
  1. Never state a live market or mandi price as current fact without an official source, location, and date. Always state that live mandi rates vary daily and suggest checking the official Agmarknet portal.
  2. Never approve, guarantee, or process bank loans, subsidies, or government scheme payouts.
  3. Never diagnose human or livestock chemical poisoning or recommend medical or antidote treatments.
- NEVER CLAIMS:
  1. Never claim guaranteed crop yields or financial returns.
  2. Never claim official government authority or sanctioning power.
- ESCALATION SCRIPT:
  When refusing out-of-scope or high-risk requests (e.g. unverified daily prices, loan approvals, severe crop disease outbreaks), state:
  "Main is specific request ke liye aapko official Krishi Vigyan Kendra (KVK) expert se connect hone ki salah dunga. Aap KVK national helpline 1800-180-1551 par call kar sakte hain." (Or in simple English: "For this specific request, I recommend consulting a local Krishi Vigyan Kendra expert via the national helpline at 1800-180-1551.")

STYLE
- Keep all spoken replies under 20 words per sentence.
- Speak naturally and conversationally for audio/voice output.
- NEVER use markdown formatting, bullet points, numbers, asterisks, brackets, or emojis.
- Be warm, patient, empathetic, and encouraging.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        # language='multi' enables multilingual streaming (Hindi + English + Hinglish) natively in nova-3
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-2.0-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Samar", 
                locale="en-IN",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()
    
    # Speak first-turn greeting automatically when connected
    await session.say("Namaste! I am Kisan Mitra, your AgriTech farming voice assistant. How can I help with your crops, pests, or advisory today?")


if __name__ == "__main__":
    cli.run_app(server)
