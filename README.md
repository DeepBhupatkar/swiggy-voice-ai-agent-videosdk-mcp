# Swiggy Voice AI Agent — Built with VideoSDK Agent Framework & MCP

> Order food, groceries, and book restaurant tables on Swiggy — using just your voice. Powered by [**VideoSDK AI Agents**](https://github.com/videosdk-live/agents), the open-source voice AI agent framework.

A real-world demonstration of how the [VideoSDK AI Agent Framework](https://github.com/videosdk-live/agents) connects to [Swiggy's MCP servers](https://github.com/Swiggy/swiggy-mcp-server-manifest) to build a fully functional **voice-powered AI agent** that works on **browser**, **phone calls (SIP)**, and **WhatsApp**.

[![VideoSDK](https://img.shields.io/badge/Framework-VideoSDK_AI_Agents-blue)](https://github.com/videosdk-live/agents)
[![Swiggy MCP](https://img.shields.io/badge/MCP-Swiggy-orange)](https://github.com/Swiggy/swiggy-mcp-server-manifest)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-support-yellow)](https://buymeacoffee.com/deepbhupatkar)

---

## Disclaimer

> This project is built **for demonstration and educational purposes only** — to showcase how the [VideoSDK AI Agent Framework](https://github.com/videosdk-live/agents) integrates with external MCP servers for voice-driven workflows.
>
> The Swiggy MCP integration is based on [Swiggy's official MCP server manifest](https://github.com/Swiggy/swiggy-mcp-server-manifest). This project is **not affiliated with, endorsed by, or a product of Swiggy**. All Swiggy trademarks belong to Swiggy. Use of Swiggy MCP servers is subject to Swiggy's terms and conditions.
>
> **Do not use this for commercial purposes.**

---

## What This Demonstrates

| Capability | How It's Used |
|-----------|--------------|
| **MCP Integration** | Connects to 3 Swiggy MCP servers with 28 real tools |
| **Voice AI Pipelines** | Agent One (multi-provider) and Agent Two (Gemini native audio) |
| **Telephony & WhatsApp** | Same agent handles browser, SIP phone calls, and WhatsApp voice |
| **Function Tools** | 28 tools across 3 services — search, cart, checkout, tracking |
| **OAuth Authentication** | Full OAuth 2.0 PKCE flow for Swiggy account access |

---

## Architecture

![VideoSDK AI Agents High Level Architecture](https://assets.videosdk.live/images/agent-architecture.png)

### End-to-End Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     User Device                                  │
│  Browser (Playground) │ Phone (SIP) │ WhatsApp                   │
└───────────┬──────────────────┬───────────────┬───────────────────┘
            │     WebRTC       │    SIP/RTP    │   Meta SIP
            ▼                  ▼               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    VideoSDK Cloud                                 │
│         Room Management │ Media Routing │ Telephony Gateway       │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Agent Worker (this project)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Pipeline                                                 │   │
│  │                                                           │   │
│  │  Deepgram STT ──► Google Gemini LLM ──► Cartesia TTS    │   │
│  │       OR           (tool calls)            OR             │   │
│  │  Gemini Native Audio (single model, lowest latency)       │   │
│  └──────────────────────┬────────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼────────────────────────────────────┐   │
│  │  SwiggyMCPServer (unified provider)                        │   │
│  │  OAuth 2.0 PKCE │ Tool Dedup │ Schema Sanitization         │   │
│  └───────┬──────────────┬─────────────────┬──────────────────┘   │
└──────────┼──────────────┼─────────────────┼──────────────────────┘
           │              │                 │
     HTTPS + OAuth   HTTPS + OAuth    HTTPS + OAuth
           │              │                 │
   ┌───────▼──────┐ ┌────▼───────┐ ┌───────▼────────┐
   │ Swiggy Food  │ │ Instamart  │ │   Dineout      │
   │  13 tools    │ │  8 tools   │ │   7 tools      │
   │ /food        │ │ /im        │ │   /dineout     │
   └──────────────┘ └────────────┘ └────────────────┘
```

### How It Works

1. **User speaks** into the Playground (browser), phone, or WhatsApp
2. **Audio** is routed through VideoSDK Cloud to the agent worker
3. **Pipeline** converts speech to text and sends it to the LLM
4. **LLM** understands intent and calls the appropriate Swiggy MCP tool
5. **SwiggyMCPServer** routes the tool call to the correct Swiggy endpoint with OAuth
6. **Real data** comes back (restaurants, menus, prices, cart status)
7. **LLM** formulates a natural response, which is spoken back to the user

---

## Services & Tools

| Service | Tools | Capabilities |
|---------|-------|-------------|
| **Food Delivery** | 13 | Search restaurants, browse menus, manage cart, apply coupons, place orders (COD), track delivery |
| **Instamart** | 8 | Search groceries by name/brand, manage cart, checkout (COD), track order |
| **Dineout** | 7 | Find nearby restaurants, check slots, book tables (free bookings) |

---

## Quick Start

### Automated Setup

```bash
git clone https://github.com/DeepBhupatkar/swiggy-voice-ai-agent-videosdk-mcp.git
cd swiggy-voice-ai-agent-videosdk-mcp
chmod +x run.sh
./run.sh
```

### Manual Setup

**1. Clone and create environment**

```bash
git clone https://github.com/DeepBhupatkar/swiggy-voice-ai-agent-videosdk-mcp.git
cd swiggy-voice-ai-agent-videosdk-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirement.txt
```

**2. Configure API keys**

```bash
cp .env.example .env
```

| Key | Provider | Required For |
|-----|----------|-------------|
| `VIDEOSDK_AUTH_TOKEN` | [app.videosdk.live](https://app.videosdk.live) | All modes |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/apikey) | All modes |
| `DEEPGRAM_API_KEY` | [console.deepgram.com](https://console.deepgram.com) | Agent One only |
| `CARTESIA_API_KEY` | [play.cartesia.ai](https://play.cartesia.ai) | Agent One only |

**3. Login to Swiggy**

```bash
python swiggy_mcp.py
```

Opens your browser for Swiggy OAuth login. Tokens saved locally — no passwords stored.

**4. Run the agent**

```bash
# Agent One — Deepgram STT + Google LLM + Cartesia TTS (richer voice)
python swiggy_agent_one.py

# Agent Two — Gemini native audio (only VideoSDK + Google keys needed)
python swiggy_agent_two.py

# Phone/WhatsApp — registers for inbound SIP calls
python swiggy_agent_phone.py
```

The agent auto-creates a meeting room with `playground=True` — no room ID needed.
A dynamic **VideoSDK Playground link** (with token & meetingId) is printed to the terminal once the agent starts — open it to talk.

**5. Talk to your agent** — open the dynamic playground link printed in the terminal

---

## Telephony & WhatsApp

The same Swiggy agent can handle **phone calls** and **WhatsApp voice** using VideoSDK's SIP telephony integration.

### Run as Phone Agent

```bash
python swiggy_agent_phone.py
```

This registers the agent with VideoSDK's telephony service using `Options(register=True)`. The agent then waits for inbound calls.

### Setup SIP Gateway (Phone Calls)

1. Get a phone number from a SIP provider (Twilio, Vonage, Telnyx, Plivo, Exotel)
2. In [VideoSDK Dashboard](https://app.videosdk.live) → **Telephony**:
   - Create an **Inbound Gateway** with your phone number
   - Create an **Outbound Gateway** with your SIP provider credentials
   - Create a **Routing Rule**: Gateway → Agent → `SwiggyVoiceAgent`
3. Configure your SIP provider to forward calls to the VideoSDK Inbound Gateway URL
4. Call your phone number — the Swiggy agent answers!

> Full guide: [AI Telephony Agent Quick Start](https://docs.videosdk.live/ai_agents/ai-phone-agent-quick-start)

### Setup WhatsApp Voice

1. You need a **Meta Business Account** with a verified WhatsApp Business phone number
2. In [VideoSDK Dashboard](https://app.videosdk.live) → **Telephony**:
   - Create an **Inbound Gateway** with your WhatsApp number
   - Create a **Routing Rule**: Gateway → Agent → `SwiggyVoiceAgent`
3. Use the Meta Graph API to enable SIP forwarding to VideoSDK:

```bash
curl --location 'https://graph.facebook.com/v19.0/{phone_number_id}/settings' \
  --header 'Authorization: Bearer {access_token}' \
  --header 'Content-Type: application/json' \
  --data '{"calling":{"status":"ENABLED","sip":{"status":"ENABLED","servers":[{"hostname":"YOUR_HOSTNAME.sip.videosdk.live"}]}}}'
```

4. Call your WhatsApp Business number — the Swiggy agent picks up!

> Full guide: [WhatsApp Agent Quick Start](https://docs.videosdk.live/ai_agents/whatsapp-voice-agent-quick-start)

### Making Outbound Calls

```bash
curl --request POST \
  --url https://api.videosdk.live/v2/sip/call \
  --header 'Authorization: YOUR_VIDEOSDK_TOKEN' \
  --header 'Content-Type: application/json' \
  --data '{"gatewayId": "your_outbound_gateway_id", "sipCallTo": "+1234567890"}'
```

---

## Project Structure

```
├── swiggy_agent_one.py      # Agent One — Deepgram STT + Google LLM + Cartesia TTS
├── swiggy_agent_two.py      # Agent Two — Gemini native audio (fewest keys, lowest latency)
├── swiggy_agent_phone.py    # Agent Phone — telephony & WhatsApp (SIP)
├── swiggy_mcp.py            # Swiggy MCP connection + OAuth 2.0 PKCE
├── instructions.py          # Agent persona, rules, and tool workflows
├── setup.sh                 # Automated setup + launch (one command to run everything)
├── requirement.txt          # Python dependencies
├── .env.example             # API key template
├── .gitignore               # Excludes secrets, venv, caches
└── swiggy.md                # Swiggy MCP reference docs
```

---

## How Authentication Works

This project connects directly to Swiggy's MCP servers — no IDE extensions required.

```
First run:
  python swiggy_mcp.py → browser opens → Swiggy login
                       → OAuth callback on localhost:8765
                       → tokens saved to .swiggy_tokens.json

Subsequent runs:
  SwiggyMCPServer reads .swiggy_tokens.json
               → auto-refreshes if expired
               → connects to mcp.swiggy.com with Bearer token
```

---

## Built With VideoSDK AI Agents

This project is built on [**VideoSDK AI Agents**](https://github.com/videosdk-live/agents) — an open-source Python framework for building real-time multimodal conversational AI agents.

**Why VideoSDK Agents?**

- **Multi-model support** — OpenAI, Google Gemini, Anthropic, AWS Nova Sonic, and more
- **20+ TTS providers** — ElevenLabs, Cartesia, OpenAI, Google, AWS Polly, etc.
- **MCP Integration** — Connect agents to external tools via Model Context Protocol
- **Telephony** — SIP phone calls and WhatsApp voice via built-in gateway support
- **A2A Protocol** — Agent-to-agent communication for complex workflows
- **Observability** — Built-in OpenTelemetry tracing and metrics

Try it yourself: [github.com/videosdk-live/agents](https://github.com/videosdk-live/agents)

---

## Important Notes

- **This is a demo** — built to showcase VideoSDK's agent framework capabilities with a real MCP integration. Not for commercial use.
- **Swiggy MCP reference**: [github.com/Swiggy/swiggy-mcp-server-manifest](https://github.com/Swiggy/swiggy-mcp-server-manifest)
- **Keep the Swiggy app closed** while using this agent — simultaneous sessions cause conflicts.
- **COD orders are real** — the agent places actual orders. Always confirm before checkout.
- **Free bookings only** for Dineout — paid reservations are not supported.

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `401 Unauthorized` | Re-run `python swiggy_mcp.py` to refresh tokens |
| Browser doesn't open for login | Copy the URL from terminal and open manually |
| Connection timeout | Check internet; Swiggy MCP may be temporarily down |
| Agent not receiving calls | Verify routing rule `agent_id` matches `SwiggyVoiceAgent` in `swiggy_agent_phone.py`. For browser agents, no room ID is needed — one is auto-generated. |

---

## Author

**Deep Bhupatkar** — Co-builder of the [VideoSDK Voice AI Agent Framework](https://github.com/videosdk-live/agents)

[![GitHub](https://img.shields.io/badge/GitHub-DeepBhupatkar-181717?logo=github)](https://github.com/DeepBhupatkar)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Deep_Bhupatkar-0A66C2?logo=linkedin)](https://www.linkedin.com/in/deep-bhupatkar/)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-support-FFDD00?logo=buymeacoffee)](https://buymeacoffee.com/deepbhupatkar)

If you found this useful, please **star this repo** and [**star the VideoSDK Agents framework**](https://github.com/videosdk-live/agents) too!

---

## License
This project is licensed under the MIT License.