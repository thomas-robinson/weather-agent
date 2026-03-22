# ⛅ Storm — Personal Meteorologist AI Agent

A **Personal Meteorologist AI Agent** built for the **NVIDIA GTC Vibe Coding Hackathon**.

Storm is powered by **NVIDIA Nemotron** (via NVIDIA NIM) as its core reasoning engine,
orchestrated with **LangGraph** in a ReAct agentic workflow. It demonstrates autonomous
reasoning, multi-step tool chaining, and real-world weather intelligence.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Gradio Chat UI                        │
│              (Chat + Sidebar Profile + Morning Briefing) │
└──────────────────────┬──────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   LangGraph     │
              │  ReAct Agent    │
              │  (graph.py)     │
              └────────┬────────┘
                       │
         ┌─────────────▼──────────────┐
         │  NVIDIA Nemotron (NIM API)  │
         │  nvidia/llama-3.1-nemotron │
         │  -nano-8b-v1               │
         │  + NeMo Guardrails         │
         └─────────────┬──────────────┘
                       │
   ┌───────────────────┼──────────────────┬──────────────┐
   │                   │                  │              │
┌──▼──────┐  ┌─────────▼────┐  ┌─────────▼───┐  ┌──────▼──────┐
│ Weather  │  │   Alerts     │  │   Airport   │  │   Route     │
│  Tools   │  │   Tool       │  │   Tool      │  │   Tool      │
├──────────┤  ├──────────────┤  ├─────────────┤  ├─────────────┤
│Open-Meteo│  │ NWS API      │  │ FAA Status  │  │ NWS + Wx    │
│(no key)  │  │(no key)      │  │ API (free)  │  │ (no key)    │
└──────────┘  └──────────────┘  └─────────────┘  └─────────────┘
                                                        │
                                               ┌────────▼────────┐
                                               │   Clothing       │
                                               │   Tool           │
                                               │ (Nemotron-       │
                                               │  powered)        │
                                               └─────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| **Current Weather** | Temperature, humidity, wind, UV index, feels-like |
| **15-min Nowcast** | "Rain starts in 8 minutes" — minute-by-minute precipitation |
| **Hourly Forecast** | Up to 48 hours: temp, precipitation probability, wind |
| **Daily Forecast** | Up to 16 days: high/low, UV, sunrise/sunset, dominant weather |
| **Weather Alerts** | Active NWS alerts: flood warnings, tornado watches, etc. |
| **Airport Delays** | FAA real-time delay status, type, and reason + airport weather |
| **Route Weather** | Weather + alerts at origin, midpoint, and destination |
| **Clothing Recommendations** | Nemotron-powered personalized outfit advice |
| **Morning Briefing** | One-click full daily intelligence briefing |
| **User Profile** | Persistent session preferences (location, style, cold sensitivity) |
| **NeMo Guardrails** | On-topic safety rails — keeps Storm focused on weather |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/thomas-robinson/weather-agent.git
cd weather-agent
pip install -r requirements.txt
```

### 2. Configure NVIDIA API Key

```bash
cp .env.example .env
# Edit .env and set your NVIDIA_API_KEY from build.nvidia.com
```

### 3. Run

```bash
python app.py
```

Open http://localhost:7860 in your browser.

---

## 📁 File Structure

```
weather-agent/
├── README.md                    # This file
├── requirements.txt             # All dependencies
├── .env.example                 # Template for API keys
├── app.py                       # Main Gradio UI application
├── agent/
│   ├── __init__.py
│   ├── graph.py                 # LangGraph ReAct agent
│   ├── state.py                 # Agent state schema
│   ├── prompts.py               # System prompts for Nemotron
│   └── llm.py                   # NVIDIA NIM LLM configuration
├── tools/
│   ├── __init__.py
│   ├── weather.py               # Weather tools (current, nowcast, hourly, daily)
│   ├── alerts.py                # NWS weather alerts
│   ├── airport.py               # FAA airport delay tool
│   ├── routing.py               # Route weather analysis
│   └── clothing.py              # Wardrobe recommendation (Nemotron-powered)
├── models/
│   ├── __init__.py
│   └── schemas.py               # Pydantic schemas
├── config/
│   ├── __init__.py
│   ├── guardrails/              # NeMo Guardrails config
│   │   ├── config.yml
│   │   └── rails.co
│   └── settings.py              # App settings and constants
└── utils/
    ├── __init__.py
    ├── geocoding.py             # geopy geocoding
    └── formatters.py            # Response formatting helpers
```

---

## 🔑 API Keys Required

| Service | Key Required | Where to Get |
|---|---|---|
| **NVIDIA NIM** | ✅ Yes | [build.nvidia.com](https://build.nvidia.com) |
| Open-Meteo | ❌ No | Free, no key |
| NWS Alerts | ❌ No | Free, no key |
| FAA Status | ❌ No | Free, no key |

---

## 🧠 NVIDIA Tools Used

| Tool | Role |
|---|---|
| **NVIDIA Nemotron Nano** (`nvidia/llama-3.1-nemotron-nano-8b-v1`) | Core LLM — all reasoning, planning, response generation |
| **NVIDIA NIM API** | Model hosting and inference endpoint |
| **langchain-nvidia-ai-endpoints** | Native LangChain integration for NIM |
| **NeMo Guardrails** | Safety and topic control |

---

## 💬 Example Queries

- "What's the weather in New York right now?"
- "Will it rain in the next 15 minutes in Seattle?"
- "Give me a 7-day forecast for Miami."
- "Are there any weather alerts for Houston, TX?"
- "What are the delays at LAX airport?"
- "Is it safe to drive from Austin to Dallas today?"
- "What should I wear in Chicago? I have a business meeting and it's cold."

---

## 🌅 Morning Briefing

Click the **☀️ Morning Briefing** button to have Storm autonomously:
1. Get current conditions at your default location
2. Get the full day forecast
3. Check weather alerts
4. Check airport delays (if you've set flight info)
5. Generate personalized clothing recommendations
6. Compile everything into a friendly, actionable daily briefing

---

## ⚙️ Configuration

All configurable values live in `config/settings.py`:
- `NIM_MODEL` — currently `nvidia/llama-3.1-nemotron-nano-8b-v1`; swap to a larger model (e.g. `nvidia/llama-3.3-nemotron-super-49b-v1`) for higher reasoning quality
- `NIM_TEMPERATURE` — controls response creativity (default 0.6)
- `NIM_MAX_TOKENS` — max response length (default 4096)
