#!/usr/bin/env bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
  ____   ___  _______       __  __  ____ ____  
 |  _ \ / _ \/ ___|___ \     |  \/  |/ ___|  _ \ 
 | |_) | | | \___ \ __) |____| |\/| | |   | |_) |
 |  _ <| |_| |___) / __/_____| |  | | |___|  __/ 
 |_| \_\\___/|____/_____|    |_|  |_|\____|_|    
                                                 
EOF
echo -e "${NC}"
echo -e "${GREEN}Installing ros2-mcp-server...${NC}"

# 1. Install via pip
if command -v pipx &> /dev/null; then
    echo -e "${YELLOW}Found pipx. Installing...${NC}"
    pipx install ros2-mcp-server || true
elif command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}Using pip3...${NC}"
    pip3 install --user ros2-mcp-server
else
    echo -e "${YELLOW}Using pip...${NC}"
    pip install --user ros2-mcp-server
fi

# 2. Inject configuration using Python
python3 -c '
import os
import json
import sys

def update_config(filepath, config_type):
    if not os.path.exists(filepath):
        return False
        
    try:
        with open(filepath, "r") as f:
            content = f.read()
            config = json.loads(content) if content.strip() else {}
    except Exception:
        config = {}

    if config_type == "claude":
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        config["mcpServers"]["ros2"] = {
            "command": "ros2-mcp-server",
            "args": ["--demo-sim"],
            "env": {"SAFETY_LEVEL": "safe_write"}
        }
    elif config_type == "antigravity":
        config["ros2"] = {
            "command": "ros2-mcp-server",
            "args": ["--demo-sim"],
            "env": {"SAFETY_LEVEL": "safe_write"}
        }

    # Backup original
    with open(filepath + ".bak", "w") as f:
        f.write(content if "content" in locals() else "")
        
    with open(filepath, "w") as f:
        json.dump(config, f, indent=2)
        
    return True

# Detect OS and paths
home = os.path.expanduser("~")
claude_paths = [
    os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json"),
    os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude_desktop_config.json"),
    os.path.join(home, ".config", "Claude", "claude_desktop_config.json")
]
antigravity_path = os.path.join(home, ".gemini", "config", "mcp_servers.json")

claude_configured = False
for p in claude_paths:
    if update_config(p, "claude"):
        print(f"✅ Configured Claude Desktop at: {p}")
        claude_configured = True
        break

if update_config(antigravity_path, "antigravity"):
    print(f"✅ Configured Antigravity IDE at: {antigravity_path}")

if not claude_configured:
    print("⚠️  Claude Desktop config not found. You may need to configure it manually.")
'

echo -e "\n${GREEN}Installation Complete! 🚀${NC}"
echo -e "You can now open Claude Desktop or Antigravity and start talking to your robot."
echo -e "Try saying: ${YELLOW}'Run a system diagnostic on the robot'${NC}"
