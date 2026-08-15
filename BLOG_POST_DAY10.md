# Day 10: Complete Blog Post & LinkedIn Sharing Kit

Congratulations on completing the **10 Days of Voice Agents — VoiceForBharat Edition**! 🚀

Below is your complete, publication-ready blog post draft and LinkedIn announcement copy for **Kisan Mitra**, your AgriTech Voice AI Assistant built with **Murf Falcon TTS**, **LiveKit Agents**, **Deepgram Nova-3**, and **Google Gemini**.

---

## Part 1: Full Blog Post Draft
*(Ready to publish on DEV Community, Hashnode, Medium, or your personal blog)*

---

# Building Kisan Mitra: An Ultra-Low Latency Multilingual Voice AI for Indian Farmers using Murf Falcon & LiveKit

*How I built an AI voice assistant for Tamil Nadu farmers with real-time mandi prices, weather forecasts, explicit consent memory, human escalation, and specialist agent handoffs over 10 days.*

---

## 1. The Problem & Target Audience

In rural India, millions of farmers face daily challenges requiring immediate, localized information:
- **Fluctuating Mandi Prices:** Farmers sell their produce at wholesale markets (mandis) without knowing current modal prices, leaving them vulnerable to middleman exploitation.
- **Micro-Climate Weather Hazards:** Spraying pesticides right before unpredicted rainfall wastes thousands of rupees in crop inputs.
- **Language & Digital Literacy Barriers:** Traditional mobile apps require navigating complex text UIs in English. For a farmer standing in a paddy field, text interfaces are impractical.

**Voice is the natural interface for rural India.**

To solve this, I built **Kisan Mitra** (கிசான் மித்ரா / Kisan Friend) during the **#VoiceForBharat 10 Days of Voice Agents Challenge**. Kisan Mitra is an ultra-low latency, voice-first AI assistant designed specifically for Tamil Nadu farmers. It speaks fluent Tamil (and English code-mixed speech), listens attentively, remembers farmer context with explicit consent, fetches real-time agricultural data, escalates emergencies to human agricultural officers (KVK), and seamlessly hands off complex crop disease queries to a specialized **Crop Doctor Agent**.

---

## 2. System Architecture & Tech Stack

Building a real-time conversational voice agent requires balancing speech-to-text (STT), reasoning (LLM), text-to-speech (TTS), and audio transport to achieve sub-second end-to-end latency.

```
       +-------------------------------------------------------+
       |                   Farmer (Caller)                     |
       +--------------------------+----------------------------+
                                  | Audio Stream (WebRTC / SIP)
                                  v
       +-------------------------------------------------------+
       |                  LiveKit Agents SDK                   |
       |            (Silero VAD + Turn Detector)               |
       +--------------------------+----------------------------+
                                  |
                +-----------------+-----------------+
                |                                   |
                v                                   v
      +-------------------+               +-------------------+
      |   Deepgram Nova-3 |               | Murf Falcon TTS   |
      |   Multilingual    |               | (Low Latency      |
      |   Speech-to-Text  |               |  Native Tamil)    |
      +---------+---------+               +---------+---------+
                |                                   ^
                | Text Stream                       | Audio Bytes
                v                                   |
       +--------------------------------------------+----------+
       |              Google Gemini 3.5 Flash               |
       |             (Kisan Mitra Orchestrator)            |
       +-------+--------------------+-------------------+------+
               |                    |                   |
               v                    v                   v
      +-----------------+  +------------------+  +-------------------+
      | SQLite Memory   |  | Open-Meteo &     |  | Human Escalation  |
      | (Farmer Profile |  | Agmarknet Tools  |  | & Discord Webhook |
      |  with Consent)  |  | (Real Weather &  |  | (KVK Officer      |
      +-----------------+  |  Mandi Prices)   |  |  Dispatches)      |
                           +------------------+  +-------------------+
```

### Core Stack:
- **Text-to-Speech (TTS):** **Murf Falcon TTS** (`livekit-murf` plugin, `voice="Anisha"`, native Tamil locale). Murf Falcon provides sub-300ms streaming TTS audio generation, enabling natural conversational flow without uncomfortable pauses.
- **Speech-to-Text (STT):** **Deepgram Nova-3** (`language="multi"`) for high-accuracy Tamil and Indian English speech recognition under noisy field conditions.
- **Brain (LLM):** **Google Gemini 3.5 Flash Lite** for fast context processing and function calling.
- **Orchestration & WebRTC:** **LiveKit Agents SDK** with **Silero VAD** (Voice Activity Detection) and **Multilingual Turn Detector** for smooth turn-taking and barge-in support.
- **Frontend UI:** Next.js with **LiveKit Agents UI** components for real-time visual feedback (audio wave visualizer, listening/thinking/speaking indicators).

---

## 3. Key Features Built Over 10 Days

### 🎙️ 1. Native Indian Voice & Authentic Script Guardrails (Day 1 & Day 2)
Generic TTS engines often pronounce romanized Indian languages (Tanglish) with an awkward Western accent. To ensure **Murf Falcon** spoke warm, authentic Tamil, I engineered strict prompt guardrails requiring all spoken Tamil output to be rendered in **pure Tamil Unicode script** (`தமிழ் எழுத்து`):

```python
# System Prompt Guardrail Rule:
SYSTEM_PROMPT = """
CRITICAL: The TTS voice is a native Tamil speaker (Murf Falcon).
For the voice to sound authentic Tamil, you MUST output every Tamil word in Tamil Unicode script.
NEVER use romanized Tamil (Tanglish).
- Greeting: வணக்கம் (NOT "Vanakkam")
- Crops: நெல் (NOT "nel"), கரும்பு (NOT "karumbu")
"""
```

### 🧠 2. Privacy-First Farmer Memory with Hard Consent Rules (Day 4)
Returning callers expect Kisan Mitra to remember their name, district, and crop history. However, privacy and trust are non-negotiable. I built an SQLite profile store backed by explicit verbal consent guardrails:

```python
@function_tool
async def save_farmer_profile(self, context: RunContext, name: str, district: str, permission_granted: bool = False) -> str:
    """Saves farmer profile ONLY if explicit permission was granted aloud."""
    if not permission_granted:
        return "ERROR: Permission denied by user. Information was NOT saved."
    # Save to SQLite database...
```
*If a farmer asks "Forget me", `forget_farmer_profile` purges their records instantly.*

### 📊 3. Live Data Tools: IMD Weather & Agmarknet Mandi Prices (Day 5)
Kisan Mitra does not hallucinate prices or weather. It invokes real-time API integrations:
- **`get_weather_forecast`:** Fetches 3-day temperature, rainfall (mm), and WMO sky condition data from Open-Meteo for 27+ Tamil Nadu districts.
- **`get_crop_market_price`:** Fetches official mandi wholesale modal, min, and max prices (in ₹/quintal) from Agmarknet (data.gov.in) for Paddy, Sugarcane, Cotton, Groundnut, Banana, Onion, and Tomato.

### 🚨 4. Human Escalation & Discord Dispatch System (Day 7)
When a farmer reports a severe crop emergency (e.g., mass wilting, locust attack) or when market data is unavailable for an urgent selling decision, Kisan Mitra escalates to a human **Krishi Vigyan Kendra (KVK)** officer:
1. Asks for explicit verbal permission to share contact details.
2. Auto-scrubs sensitive PII (OTPs, Aadhaar, account numbers) using regex sanitization.
3. Generates a unique tracking reference (e.g., `KM-20260812-0001`).
4. Fires a rich **Discord Webhook** notification to the KVK alert channel.

### 📈 5. Telemetry & Call Analytics Dashboard (Day 8)
Every session automatically records call duration, channel (Browser vs SIP telephony), tools invoked, topics covered, and outcome status (`success` vs `failed`). Early hangups (<10s) are tagged for quality analysis.

### 👨‍⚕️ 6. Bidirectional Specialist Agent Handoff (Day 9)
When a caller presents a complex pest or plant pathology query, Kisan Mitra performs a live stateful handoff to the **Crop Doctor Agent** (`CropDoctorAgent`) using `ctx.session.update_agent()`:

```python
@function_tool
async def hand_off_to_crop_doctor(self, context: RunContext, disease_or_pest_query: str = "") -> str:
    """Hands off caller to Specialist Crop Doctor Agent."""
    specialist = CropDoctorAgent(
        current_user_id=self.current_user_id,
        session_id=self.session_id,
        disease_query=disease_or_pest_query
    )
    context.session.update_agent(specialist)
    return "HANDOFF_SUCCESS: Transferred to CropDoctorAgent."
```
Once pest treatment guidance is completed, the specialist agent hands the caller back to Kisan Mitra.

---

## 4. Challenges & Engineering Solutions

### Challenge 1: Tanglish Phonetic Distortion in TTS
*Problem:* When the LLM output romanized Tamil ("Vanakkam ayya, Unga nel payiru ku..."), Murf Falcon read the characters using English phonetic rules, resulting in an unnatural accent.
*Solution:* Enforced strict Tamil Unicode generation in the LLM system prompt. Murf Falcon receives `வணக்கம் ஐயா, உங்கள் நெல் பயிருக்கு...` and outputs native Indian Tamil speech.

### Challenge 2: Voice Activity Detection & Interruption Handling
*Problem:* In noisy rural environments, ambient background noise triggered false speech interruptions.
*Solution:* Tuned **Silero VAD** thresholds, implemented `BVCTelephony` noise suppression for SIP callers, enabled preemptive generation, and set `SentenceTokenizer(min_sentence_len=2)` to prevent sentence clipping.

---

## 5. How to Build & Run Kisan Mitra

Want to run Kisan Mitra locally? Follow these quick steps:

### Prerequisites:
- Python 3.10+ with `uv`
- Node.js 18+ with `pnpm`
- Free API keys for LiveKit, Murf AI, Deepgram, and Google Gemini

### Step 1: Clone & Configure Environment
```bash
git clone https://github.com/<your-username>/murf-livekit-starter.git
cd murf-livekit-starter
```

Copy environment templates:
```bash
# Backend configuration
cp backend/.env.example backend/.env.local
```

Add your keys in `backend/.env.local`:
```env
LIVEKIT_URL=wss://your-livekit-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
MURF_API_KEY=your_murf_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
GOOGLE_API_KEY=your_gemini_api_key
```

### Step 2: Start Backend Agent
```bash
cd backend
uv sync
uv run python src/agent.py dev
```

### Step 3: Start Frontend UI
In a second terminal:
```bash
cd frontend
pnpm install
pnpm dev
```
Open `http://localhost:3000` in your browser, hit **Connect**, and speak to Kisan Mitra in Tamil or English!

---

## 6. What's Next?
- **WhatsApp Audio Note Integration:** Allowing farmers to send voice notes over WhatsApp and receive voice replies.
- **Multilingual Support for Kannada & Telugu:** Expanding Murf Falcon voices to cover all South Indian farming belts.
- **Offline Mandi Price Caching:** Enhancing resiliency for low-connectivity regions.

---

## 7. Code Repository & Acknowledgments

- **GitHub Repository:** [https://github.com/<your-username>/murf-livekit-starter](https://github.com/<your-username>/murf-livekit-starter) *(Replace with your GitHub repo URL)*
- **Murf Falcon Documentation:** [https://murf.ai/api/docs/text-to-speech/streaming](https://murf.ai/api/docs/text-to-speech/streaming)
- **LiveKit Agents SDK:** [https://docs.livekit.io/agents](https://docs.livekit.io/agents)

Huge thanks to **Murf AI** and the **VoiceForBharat** initiative for powering this 10-day challenge!

---

---

## Part 2: Ready-to-Post LinkedIn Copy
*(Copy and paste this into LinkedIn)*

---

🌾 **Day 10 / 10: I built Kisan Mitra — an AI Voice Assistant for Indian Farmers!** 🚀

Over the last 10 days, I participated in the **#VoiceForBharat** challenge and built **Kisan Mitra** (கிசான் மித்ரா), a real-time, voice-first AI assistant powered by **Murf Falcon TTS** and **LiveKit Agents**.

Voice is the ultimate equalizer for rural India. Tamil Nadu farmers can now talk directly to Kisan Mitra to get real-time mandi prices, localized weather forecasts, government scheme advice, and instant crop disease guidance — without touching a text interface!

### 🌟 Key Highlights of What I Built:
1. **Ultra-Low Latency Indian Accent Voice:** Powered by **Murf Falcon TTS** for sub-second, native Tamil speech generation.
2. **Authentic Script Formatting:** Prompt-engineered Tamil Unicode guardrails so the agent speaks natural, accent-free Tamil.
3. **Privacy & Explicit Consent Memory:** SQLite database that only saves caller profiles when permission is explicitly granted aloud.
4. **Real-Data Tools:** Live integration with Open-Meteo weather forecasts and official data.gov.in Agmarknet mandi wholesale prices.
5. **Human Escalation & Discord Alerts:** Auto-scrubs PII and dispatches urgent crop emergency alerts to human KVK agricultural officers.
6. **Specialist Handoff:** Bidirectional context-aware handoff between Kisan Mitra and a specialized Crop Doctor Agent for pest disease diagnosis.

### 🛠️ Tech Stack:
- **TTS:** Murf Falcon (`livekit-murf`)
- **STT:** Deepgram Nova-3
- **LLM:** Google Gemini 3.5 Flash
- **Transport:** LiveKit Agents SDK (WebRTC)

Sharing my complete journey, architecture breakdown, and step-by-step setup guide in my latest blog post below! 👇

🔗 **Read the full blog post & inspect the code:** [Insert your blog link here]
📁 **GitHub Repo:** [Insert your public repo link here]

A huge thank you to **@Murf AI** for hosting **10 Days of Voice Agents — VoiceForBharat Edition** and providing the fastest TTS engine on the market!

#VoiceForBharat #MurfAI #VoiceAI #GenerativeAI #LiveKit #AgriTech #BuildInPublic #ArtificialIntelligence #VoiceAgents #Python #NextJS

---

---

## Part 3: Submission Checklist & Next Steps

To complete your submission:
1. **Publish the Blog Post:** Copy Part 1 to [DEV Community](https://dev.to/), [Hashnode](https://hashnode.com/), or [Medium](https://medium.com/).
   - Replace `<your-username>` with your GitHub handle in all link placeholders.
2. **Post on LinkedIn:** Copy Part 2 to LinkedIn, add your published blog link and GitHub repository link, tag **@Murf AI**, and publish.
3. **Submit on Discord:** Copy your LinkedIn post link and submit it using the submission form link shared on the Murf AI Discord server.

🎉 **Congratulations on finishing all 10 Days of Voice Agents!**
