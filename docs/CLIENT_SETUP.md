# 🌐 Client Integration Guides: Connecting 1000+ AI Models

`ros2-mcp-server` follows the standard **Model Context Protocol (MCP)** specification (2024-11-05). It allows any AI client or LLM framework—supporting over **1000+ AI models** (Claude 3.5, GPT-4o, Gemini 2.0, DeepSeek R1, Llama 3)—to connect directly to physical robots and ROS2 simulations.

---

## 1. 🤖 Claude Desktop & Claude Code CLI

### Automatic 1-Line Setup
```bash
curl -sSL https://raw.githubusercontent.com/EngineerAbdullahBinZafar/ros2-mcp-server/main/install.sh | bash
```

### Manual Configuration
Edit `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ros2": {
      "command": "ros2-mcp-server",
      "env": {
        "SAFETY_LEVEL": "safe_write"
      }
    }
  }
}
```

---

## 2. ⚡ Cursor IDE & Windsurf

In Cursor or Windsurf settings:
1. Navigate to **Features → MCP Servers**.
2. Click **+ Add New MCP Server**.
3. Set **Name**: `ros2`
4. Set **Type**: `command`
5. Set **Command**: `ros2-mcp-server --demo-sim`

---

## 3. 🚀 Antigravity IDE

Edit `~/.gemini/config/mcp_servers.json`:
```json
{
  "ros2": {
    "command": "ros2-mcp-server",
    "env": {
      "SAFETY_LEVEL": "safe_write"
    }
  }
}
```

---

## 4. 💻 VS Code (Roo Code / Cline / Continue.dev)

Add to `cline_mcp_settings.json` or Roo Code settings:
```json
{
  "mcpServers": {
    "ros2-robotics": {
      "command": "ros2-mcp-server",
      "args": ["--safety-level", "safe_write"]
    }
  }
}
```

---

## 5. 🐍 OpenAI Agents SDK & LangChain / LlamaIndex

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="ros2-mcp-server",
        args=["--demo-sim"],
        env={"SAFETY_LEVEL": "safe_write"}
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools (16 tools)
            tools = await session.list_tools()
            print(f"Connected to ros2-mcp-server | Tools: {len(tools.tools)}")
            
            # Call system diagnostics
            result = await session.call_tool("system_diagnostics", {})
            print(result.content[0].text)

asyncio.run(main())
```

---

## 🦙 Local Models via Ollama / LM Studio

You can connect local open-source models (Llama 3.3, Qwen 2.5, DeepSeek R1) via any MCP-enabled proxy adapter:
```bash
SAFETY_LEVEL=safe_write ros2-mcp-server --demo-sim
```
