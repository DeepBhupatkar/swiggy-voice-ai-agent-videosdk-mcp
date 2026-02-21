"""
Swiggy MCP — OAuth + unified MCP connection layer.

Handles the full OAuth 2.0 + PKCE flow for Swiggy MCP servers:
  1. First run: opens browser for Swiggy login, stores tokens locally
  2. Subsequent runs: reuses stored tokens (auto-refreshes if expired)

Usage:
  - Run standalone to login:  python swiggy_mcp.py
  - Import in agent code:     from swiggy_mcp import build_swiggy_mcp_servers
"""

import asyncio
import json
import logging
import webbrowser
from contextlib import AsyncExitStack
from pathlib import Path
from datetime import timedelta
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.auth import OAuthClientMetadata, OAuthClientInformationFull, OAuthToken
from mcp import ClientSession

from videosdk.agents.mcp.mcp_server import MCPServiceProvider
from videosdk.agents.utils import create_generic_mcp_adapter, ToolError

logger = logging.getLogger(__name__)

TOKEN_FILE = Path(__file__).parent / ".swiggy_tokens.json"
CALLBACK_PORT = 8765
CALLBACK_PATH = "/callback"
REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}{CALLBACK_PATH}"

SWIGGY_MCP_ENDPOINTS = {
    "swiggy-food": "https://mcp.swiggy.com/food",
    "swiggy-instamart": "https://mcp.swiggy.com/im",
    "swiggy-dineout": "https://mcp.swiggy.com/dineout",
}


# =============================================================
#  Token Storage (persists to .swiggy_tokens.json)
# =============================================================

class FileTokenStorage(TokenStorage):
    """Stores OAuth tokens and client info in a local JSON file."""

    def __init__(self, path: Path = TOKEN_FILE):
        self._path = path
        self._data = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self):
        self._path.write_text(json.dumps(self._data, indent=2, default=str))

    async def get_tokens(self) -> OAuthToken | None:
        raw = self._data.get("tokens")
        if raw:
            return OAuthToken(**raw)
        return None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._data["tokens"] = tokens.model_dump()
        self._save()
        logger.info("Tokens saved successfully")

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        raw = self._data.get("client_info")
        if raw:
            return OAuthClientInformationFull(**raw)
        return None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._data["client_info"] = client_info.model_dump()
        self._save()
        logger.info("Client info saved")


# =============================================================
#  OAuth Callback Handlers
# =============================================================

_auth_result = {"code": None, "state": None, "event": threading.Event()}


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        if code:
            _auth_result["code"] = code
            _auth_result["state"] = state
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family:sans-serif;text-align:center;padding:60px">
                <h2>Swiggy Login Successful!</h2>
                <p>You can close this tab and go back to the terminal.</p>
                </body></html>
            """)
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h2>Login Failed: {error}</h2></body></html>".encode())

        _auth_result["event"].set()

    def log_message(self, format, *args):
        pass


async def _redirect_handler(auth_url: str) -> None:
    """Opens the Swiggy login page in the user's browser."""
    logger.info(f"Opening browser for Swiggy login...")
    print(f"\nOpening browser for Swiggy login...")
    print(f"If it doesn't open automatically, go to:\n{auth_url}\n")
    webbrowser.open(auth_url)


async def _callback_handler() -> tuple[str, str | None]:
    """Runs a local HTTP server to catch the OAuth callback."""
    _auth_result["code"] = None
    _auth_result["state"] = None
    _auth_result["event"].clear()

    server = HTTPServer(("localhost", CALLBACK_PORT), _CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    logger.info(f"Waiting for OAuth callback on localhost:{CALLBACK_PORT}...")
    print(f"Waiting for login callback on localhost:{CALLBACK_PORT}...")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _auth_result["event"].wait)

    server.shutdown()

    code = _auth_result["code"]
    state = _auth_result["state"]

    if not code:
        raise RuntimeError("OAuth callback did not receive an authorization code")

    logger.info("Received OAuth callback successfully")
    return code, state


# =============================================================
#  OAuth Provider Factory
# =============================================================

def create_oauth_provider(server_url: str = "https://mcp.swiggy.com") -> OAuthClientProvider:
    """Create an OAuthClientProvider for Swiggy MCP."""
    storage = FileTokenStorage()

    client_metadata = OAuthClientMetadata(
        redirect_uris=[REDIRECT_URI],
        token_endpoint_auth_method="none",
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        client_name="Swiggy Voice Agent",
        scope="mcp:tools mcp:resources mcp:prompts",
    )

    return OAuthClientProvider(
        server_url=server_url,
        client_metadata=client_metadata,
        storage=storage,
        redirect_handler=_redirect_handler,
        callback_handler=_callback_handler,
        timeout=120.0,
    )


# =============================================================
#  Schema Sanitization (Google LLM compatibility)
# =============================================================

def _sanitize_schema(schema: dict) -> dict:
    """Recursively normalize schema types and enums for Google LLM compatibility.
    Handles list-typed 'type' fields and unhashable enum values."""
    if not isinstance(schema, dict):
        return schema
    cleaned = {}
    for k, v in schema.items():
        if isinstance(v, dict):
            cleaned[k] = _sanitize_schema(v)
        elif isinstance(v, list) and k == "type":
            cleaned[k] = v[0] if len(v) == 1 else "string"
        elif isinstance(v, list) and k == "enum":
            cleaned[k] = [str(x) for x in v]
        else:
            cleaned[k] = v
    if "properties" in cleaned and isinstance(cleaned["properties"], dict):
        for prop_name, prop_val in cleaned["properties"].items():
            cleaned["properties"][prop_name] = _sanitize_schema(prop_val)
    return cleaned


# =============================================================
#  Tool Executor (routes calls to the correct session)
# =============================================================

async def _route_tool_call(tool_executor, session, tool_name, parameters):
    """Execute a tool call on the correct Swiggy MCP session."""
    try:
        result = await session.call_tool(tool_name, parameters)
        return tool_executor._process_tool_result(tool_name, result)
    except ToolError:
        raise
    except Exception as e:
        raise ToolError(f"Tool execution failed for '{tool_name}': {str(e)}")


# =============================================================
#  Unified Swiggy MCP Server
# =============================================================

class SwiggyMCPServer(MCPServiceProvider):
    """Unified MCP provider for all Swiggy services (Food, Instamart, Dineout).

    Connects to all 3 Swiggy MCP endpoints internally and presents a single
    deduplicated, schema-sanitized tool list to the VideoSDK agent framework.

    Since this is a single MCPServiceProvider instance, the framework's standard
    add_server() flow works correctly — one provider, one call, no duplicates.
    """

    def __init__(self):
        super().__init__(connection_timeout=300.0)
        self.auth = create_oauth_provider()
        self._extra_sessions: dict[str, ClientSession] = {}
        self._extra_stacks: list[AsyncExitStack] = []

    def get_stream_provider(self):
        """Primary connection uses the swiggy-food endpoint."""
        return streamablehttp_client(
            url=SWIGGY_MCP_ENDPOINTS["swiggy-food"],
            timeout=timedelta(seconds=30),
            sse_read_timeout=timedelta(seconds=300),
            auth=self.auth,
        )

    async def connect(self):
        """Connect to all 3 Swiggy MCP endpoints with shared OAuth."""
        await super().connect()
        logger.info("Connected to swiggy-food (primary)")

        for name, url in SWIGGY_MCP_ENDPOINTS.items():
            if name == "swiggy-food":
                continue
            stack = AsyncExitStack()
            self._extra_stacks.append(stack)
            streams = await stack.enter_async_context(
                streamablehttp_client(
                    url=url,
                    timeout=timedelta(seconds=30),
                    sse_read_timeout=timedelta(seconds=300),
                    auth=self.auth,
                )
            )
            session = await stack.enter_async_context(
                ClientSession(
                    streams[0], streams[1],
                    read_timeout_seconds=timedelta(seconds=300),
                )
            )
            await session.initialize()
            self._extra_sessions[name] = session
            logger.info(f"Connected to {name} ({url})")

    async def get_available_tools(self):
        """Gather tools from all 3 endpoints, deduplicate and sanitize schemas."""
        if not self.is_ready:
            raise RuntimeError("Not connected")

        if self.tool_registry.has_valid_cache():
            return self.tool_registry.get_cached_tools()

        all_sessions = {"swiggy-food": self.connection_mgr.session}
        all_sessions.update(self._extra_sessions)

        seen_names: set[str] = set()
        framework_tools = []

        for svc_name, session in all_sessions.items():
            mcp_tools = await session.list_tools()

            for tool in mcp_tools.tools:
                if tool.name in seen_names:
                    logger.info(f"Skipping duplicate '{tool.name}' from {svc_name}")
                    continue
                seen_names.add(tool.name)

                schema = _sanitize_schema(tool.inputSchema or {})
                executor = partial(
                    _route_tool_call, self.tool_executor, session, tool.name
                )

                adapted = create_generic_mcp_adapter(
                    tool_name=tool.name,
                    tool_description=tool.description,
                    input_schema=schema,
                    client_call_function=executor,
                )
                framework_tools.append(adapted)

        self.tool_registry.update_cache(framework_tools)
        logger.info(
            f"Registered {len(framework_tools)} unique Swiggy tools "
            f"across {len(all_sessions)} services"
        )
        return framework_tools

    async def disconnect(self):
        """Disconnect from all Swiggy endpoints."""
        for stack in self._extra_stacks:
            try:
                await stack.aclose()
            except Exception as e:
                logger.warning(f"Error closing extra session: {e}")
        self._extra_sessions.clear()
        self._extra_stacks.clear()
        await super().disconnect()

    def __repr__(self):
        return f"SwiggyMCPServer(services={list(SWIGGY_MCP_ENDPOINTS.keys())})"


def build_swiggy_mcp_servers() -> list[SwiggyMCPServer]:
    """Build a single unified MCP server for all Swiggy services."""
    server = SwiggyMCPServer()
    logger.info(f"Configured unified Swiggy MCP: {list(SWIGGY_MCP_ENDPOINTS.keys())}")
    return [server]


# =============================================================
#  Standalone Login (run this to auth before using the agent)
# =============================================================

async def _test_login():
    """Test OAuth by connecting to swiggy-food and listing tools."""
    print("=" * 50)
    print("  SWIGGY MCP LOGIN")
    print("=" * 50)

    url = SWIGGY_MCP_ENDPOINTS["swiggy-food"]
    auth = create_oauth_provider()

    print(f"\nConnecting to {url}...")
    async with streamablehttp_client(url=url, timeout=timedelta(seconds=30), sse_read_timeout=timedelta(seconds=60), auth=auth) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"\nLogin successful! Found {len(tools.tools)} tools:")
            for t in tools.tools:
                print(f"  - {t.name}: {(t.description or '')[:60]}")

    print(f"\nTokens saved to: {TOKEN_FILE}")
    print("You can now run the agent — it will reuse this login.\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test_login())
