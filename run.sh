set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
PURPLE="\033[38;5;183m"
DIM="\033[2m"
RESET="\033[0m"

echo ""
echo -e "${PURPLE}${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${PURPLE}${BOLD}║                                                              ║${RESET}"
echo -e "${PURPLE}${BOLD}║   Swiggy Voice Agent — Setup                                 ║${RESET}"
echo -e "${PURPLE}${BOLD}║   Order food, groceries & book tables by voice               ║${RESET}"
echo -e "${PURPLE}${BOLD}║                                                              ║${RESET}"
echo -e "${PURPLE}${BOLD}║   Powered by VideoSDK Voice AI Agent Framework               ║${RESET}"
echo -e "${PURPLE}${BOLD}║   ${DIM}https://github.com/videosdk-live/agents${RESET}${PURPLE}${BOLD}                    ║${RESET}"
echo -e "${PURPLE}${BOLD}║                                                              ║${RESET}"
echo -e "${PURPLE}${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# ─── Step 1: Python check ────────────────────────────────────────────
echo -e "${PURPLE}[1/6]${RESET} ${BOLD}Checking Python version...${RESET}"

PYTHON=""
for cmd in python3.12 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}ERROR: Python 3.10+ is required. Install from https://python.org${RESET}"
    exit 1
fi
echo -e "  ${GREEN}Found: $($PYTHON --version)${RESET}"

# ─── Step 2: Create virtual environment ──────────────────────────────
echo ""
echo -e "${PURPLE}[2/6]${RESET} ${BOLD}Creating virtual environment...${RESET}"

if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo -e "  ${GREEN}Created venv/${RESET}"
else
    echo -e "  ${YELLOW}venv/ already exists, reusing${RESET}"
fi

source venv/bin/activate
echo -e "  Activated: $(which python)"

# ─── Step 3: Install dependencies ────────────────────────────────────
echo ""
echo -e "${PURPLE}[3/6]${RESET} ${BOLD}Installing dependencies...${RESET}"
echo -e "  ${DIM}This may take a few minutes on first run (downloading Videosdk SDKs Agent Framework and supported plugins, etc.)${RESET}"
echo ""

pip install --upgrade pip
echo ""
pip install -r requirement.txt

echo ""
echo -e "  ${GREEN}All packages installed${RESET}"

# ─── Step 4: Configure API keys ─────────────────────────────────────
echo ""
echo -e "${PURPLE}[4/6]${RESET} ${BOLD}Configuring API keys...${RESET}"
echo ""

SKIP_ENV=""
if [ -f ".env" ]; then
    echo -e "  ${YELLOW}.env file already exists.${RESET}"
    read -rp "  Overwrite with fresh config? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo -e "  Keeping existing .env"
        SKIP_ENV=true
    fi
fi

if [ "${SKIP_ENV}" != "true" ]; then
    echo -e "  ${BOLD}You'll need API keys from these providers:${RESET}"
    echo ""
    echo -e "    ${PURPLE}•${RESET} VideoSDK  → ${PURPLE}https://app.videosdk.live${RESET}"
    echo -e "    ${PURPLE}•${RESET} Google    → ${PURPLE}https://aistudio.google.com/apikey${RESET}"
    echo -e "    ${PURPLE}•${RESET} Deepgram  → ${PURPLE}https://console.deepgram.com${RESET}  ${DIM}(Agent One only)${RESET}"
    echo -e "    ${PURPLE}•${RESET} Cartesia  → ${PURPLE}https://play.cartesia.ai${RESET}      ${DIM}(Agent One only)${RESET}"
    echo ""

    read -rp "  VideoSDK Auth Token: " VIDEOSDK_TOKEN
    read -rp "  Google API Key: " GOOGLE_KEY
    read -rp "  Deepgram API Key (Enter to skip): " DEEPGRAM_KEY
    read -rp "  Cartesia API Key (Enter to skip): " CARTESIA_KEY

    cat > .env <<EOF
VIDEOSDK_AUTH_TOKEN=${VIDEOSDK_TOKEN}
GOOGLE_API_KEY=${GOOGLE_KEY}
DEEPGRAM_API_KEY=${DEEPGRAM_KEY}
CARTESIA_API_KEY=${CARTESIA_KEY}
EOF

    echo ""
    echo -e "  ${GREEN}.env file created${RESET}"
fi

# ─── Step 5: Swiggy account login ───────────────────────────────────
echo ""
echo -e "${PURPLE}[5/6]${RESET} ${BOLD}Swiggy account login...${RESET}"
echo ""

SKIP_LOGIN=""
if [ -f ".swiggy_tokens.json" ]; then
    echo -e "  ${YELLOW}Swiggy tokens already exist (.swiggy_tokens.json)${RESET}"
    read -rp "  Re-login? (y/N): " re_login
    if [[ ! "$re_login" =~ ^[Yy]$ ]]; then
        echo -e "  Keeping existing tokens"
        SKIP_LOGIN=true
    fi
fi

if [ "${SKIP_LOGIN}" != "true" ]; then
    echo -e "  This will open your browser to log into your Swiggy account."
    echo -e "  Your session tokens are stored locally in .swiggy_tokens.json"
    echo -e "  ${YELLOW}(no passwords are saved — only OAuth tokens)${RESET}"
    echo -e "  ${DIM}Note: Swiggy MCP connection may take 1-2 minutes to establish${RESET}"
    echo ""
    read -rp "  Ready to login? (Y/n): " do_login

    if [[ ! "$do_login" =~ ^[Nn]$ ]]; then
        python swiggy_mcp.py
        echo ""
        echo -e "  ${GREEN}Swiggy login complete!${RESET}"
    else
        echo -e "  ${YELLOW}Skipped. Run 'python swiggy_mcp.py' later to login.${RESET}"
    fi
fi

# ─── Step 6: Launch the agent ────────────────────────────────────────
echo ""
echo -e "${PURPLE}${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${PURPLE}${BOLD}║  ${GREEN}Setup complete!${RESET}${PURPLE}${BOLD}                                              ║${RESET}"
echo -e "${PURPLE}${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${PURPLE}[6/6]${RESET} ${BOLD}Launch Swiggy Voice Agent${RESET}"
echo ""
echo -e "  ${PURPLE}1)${RESET} Agent One — Deepgram STT + Google LLM + Cartesia TTS  ${DIM}(all 4 keys)${RESET}"
echo -e "  ${PURPLE}2)${RESET} Agent Two — Gemini native audio  ${DIM}(only VideoSDK + Google keys)${RESET}"
echo -e "  ${PURPLE}3)${RESET} Skip — I'll run it later"
echo ""
read -rp "  Choose [1/2/3] (default: 1): " agent_choice

case "$agent_choice" in
    2)
        AGENT_FILE="swiggy_agent_two.py"
        AGENT_NAME="Agent Two"
        ;;
    3)
        echo ""
        echo -e "  ${BOLD}To run manually:${RESET}"
        echo ""
        echo -e "    source venv/bin/activate"
        echo ""
        echo -e "    ${PURPLE}# Agent One — Deepgram + Gemini + Cartesia${RESET}"
        echo -e "    python swiggy_agent_one.py"
        echo ""
        echo -e "    ${PURPLE}# Agent Two — Gemini native audio (VideoSDK + Google keys)${RESET}"
        echo -e "    python swiggy_agent_two.py"
        echo ""
        echo -e "    ${PURPLE}# Phone/WhatsApp — SIP telephony${RESET}"
        echo -e "    python swiggy_agent_phone.py"
        echo ""
        echo -e "  A dynamic ${BOLD}VideoSDK Playground${RESET} link will be printed once the agent starts."
        echo ""
        echo -e "  ${BOLD}Framework:${RESET} ${PURPLE}https://github.com/videosdk-live/agents${RESET}"
        echo ""
        exit 0
        ;;
    *)
        AGENT_FILE="swiggy_agent_one.py"
        AGENT_NAME="Agent One"
        ;;
esac

echo ""
echo -e "  Starting ${BOLD}${PURPLE}${AGENT_NAME}${RESET} ..."
echo -e "  ${DIM}Swiggy MCP connection may take 1-2 minutes on first participant join${RESET}"
echo ""
echo -e "  A dynamic ${BOLD}VideoSDK Playground${RESET} link (with token & meetingId) will appear below."
echo -e "  Open it in your browser to start talking to the agent."
echo ""
echo -e "  ${DIM}Press Ctrl+C to stop the agent${RESET}"
echo ""

python "$AGENT_FILE"
