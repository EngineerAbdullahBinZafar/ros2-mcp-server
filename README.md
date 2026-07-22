<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=0:0d1117,50:00d4ff,100:0055ff&height=200&section=header&text=ros2-mcp-server&fontSize=52&fontColor=ffffff&fontAlignY=45&desc=Connect%20Claude%20%26%20AI%20Agents%20to%20Real%20Robots%20via%20MCP&descSize=18&descAlignY=68&descColor=c9d1d9&animation=fadeIn" />

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-00d4ff.svg?style=for-the-badge&labelColor=0d1117)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=0d1117)](https://python.org)
[![ROS2](https://img.shields.io/badge/ROS2-Humble%20%7C%20Jazzy-22314E?style=for-the-badge&logo=ros&logoColor=white&labelColor=0d1117)](https://docs.ros.org)
[![MCP](https://img.shields.io/badge/Protocol-MCP%202024--11--05-0055ff?style=for-the-badge&labelColor=0d1117)](https://spec.modelcontextprotocol.io)
[![Stars](https://img.shields.io/github/stars/EngineerAbdullahBinZafar/ros2-mcp-server?style=for-the-badge&color=00d4ff&labelColor=0d1117)](https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server/stargazers)

**The world's first Model Context Protocol server for ROS2.**  
Give Claude, Antigravity, and any AI agent direct, sandboxed access to live robots.

[📖 Docs](#-how-it-works) · [⚡ Quick Start](#-quick-start-60-seconds) · [🛠️ Tools](#%EF%B8%8F-available-mcp-tools) · [🔒 Safety](#-safety--sandbox) · [💬 Community](#-community)

</div>

---

## 🧠 What This Solves

Every robotics engineer has hit this wall:

> *"I want to ask Claude why my drone is oscillating — but I can't paste 10,000 lines of ROS2 topic data into a chat window."*

**`ros2-mcp-server`** solves this permanently. It creates a **live, bidirectional bridge** between any MCP-compatible AI agent and a running ROS2 system, so the AI can:

- 📡 **Read live sensor data** directly from `/scan`, `/imu/data`, `/battery_state`
- 🎛️ **Tune PID gains** in real-time by modifying controller node parameters
- 🔍 **Run instant diagnostics** — battery level, obstacle detection, IMU health in one call
- 🤖 **Publish velocity commands** (safely sandboxed)
- 🧩 **Introspect nodes and topics** across the full ROS2 graph

No copy-pasting sensor dumps. No manual parameter editing. Just natural language conversations with your robot.

---

## ⚡ Quick Start (60 Seconds)

### 1. Install

```bash
pip install ros2-mcp-server
```

> **No ROS2 installed?** The server automatically falls back to **simulation mode** — generating realistic synthetic sensor data for development and testing.

### 2. Configure Your AI Client

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

**Antigravity IDE** (`.gemini/config/mcp_servers.json`):
```json
{
  "ros2": {
    "command": "ros2-mcp-server",
    "env": { "SAFETY_LEVEL": "safe_write" }
  }
}
```

**OpenAI Agents SDK** / **Any MCP Client**:
```bash
SAFETY_LEVEL=safe_write ros2-mcp-server
```

### 3. Talk to Your Robot

Open Claude or Antigravity and ask naturally:

```
"What's the current battery level on the robot?"
"My drone is oscillating on the pitch axis — check the IMU and help me tune the PID."
"Is there any obstacle within 1 metre?"
"Set max_vel_x to 0.3 on the nav2 controller."
```

---

## 🛠️ Available MCP Tools

The server exposes **11 tools** that AI agents can call:

| Tool | Description |
| :--- | :--- |
| `system_diagnostics` | **Instant full health check.** Battery, LiDAR, IMU, node count, critical issues. |
| `list_topics` | List all active ROS2 topics with message types. |
| `read_topic` | Read the latest message from any topic (`/scan`, `/imu/data`, etc.). |
| `get_robot_snapshot` | Fetch LiDAR + IMU + Battery + Odometry in one efficient call. |
| `publish_topic` | Publish to any allowlisted topic (e.g. `/cmd_vel`, `/arm_target_angle`). |
| `list_nodes` | List all currently running ROS2 nodes. |
| `get_node_info` | Inspect a specific node and find its related topics. |
| `get_parameter` | Read a live parameter from any running node (PID gains, velocity limits). |
| `set_parameter` | Dynamically update a node parameter (sandboxed). |
| `get_pid_state` | Read current Kp, Ki, Kd from a controller node. |
| `tune_pid` | Apply new PID gains with built-in engineering guidance. |

---

## 🔒 Safety & Sandbox

`ros2-mcp-server` has a **three-tier execution sandbox** that prevents AI agents from sending destructive commands to hardware:

| Level | Set Via | Effect |
| :--- | :--- | :--- |
| `read_only` | `SAFETY_LEVEL=read_only` | AI can only read — zero writes to hardware |
| `safe_write` | `SAFETY_LEVEL=safe_write` *(default)* | Writes restricted to an explicit topic/param allowlist |
| `full` | `SAFETY_LEVEL=full` | Unrestricted access — use only in simulation |

**Customizing the allowlist** (in your launch script):
```python
from ros2_mcp.sandbox import CommandSandbox, SafetyLevel

sandbox = CommandSandbox(SafetyLevel.SAFE_WRITE)
sandbox.allow_topic("/my_custom_actuator")
sandbox.allow_param("my_node", "target_speed")
```

Every action is recorded in a full **audit log** — every allow and block decision, timestamped and retrievable:
```python
print(sandbox.get_audit_log())
```

---

## 🔌 Transport Modes

| Mode | How to Activate | When to Use |
| :--- | :--- | :--- |
| **Native rclpy** | Source ROS2 before running | On-robot deployment (Jetson, RPi) |
| **Simulation** | Default (auto-detected) | Development without hardware |
| **rosbridge (WS)** | `pip install ros2-mcp-server[rosbridge]` | Remote laptop → real robot |

---

## 💬 Example AI Conversation

```
User:  My autonomous drone stopped responding. What's wrong?

Claude: I'll run a full system diagnostic.
        [calls system_diagnostics]

        CRITICAL: Battery at 18% (21.2V) — return to base immediately.
        WARNING: Closest obstacle detected at 0.42m.
        IMU Z-acceleration: 9.79 m/s² (nominal).
        Active nodes: 8 running.

        The primary issue is a critically low battery. Land immediately.
        Secondary: There's an obstacle at 42cm — likely preventing forward motion.
        Should I halt all velocity commands via /cmd_vel?

User:  Yes, stop it.

Claude: [calls publish_topic → /cmd_vel → {linear_x: 0, angular_z: 0}]
        Done. Robot velocity commands halted. Land safely.
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│            AI Agent (Claude / Antigravity)  │
│                                             │
│  "Check battery and tune PID"               │
└────────────────────┬────────────────────────┘
                     │  MCP stdio / JSON-RPC 2.0
┌────────────────────▼────────────────────────┐
│           ros2-mcp-server                   │
│                                             │
│  ┌─────────────┐   ┌────────────────────┐  │
│  │  MCP Server │   │  CommandSandbox    │  │
│  │  (11 tools) │   │  (Safety Filter)   │  │
│  └──────┬──────┘   └────────┬───────────┘  │
│         │                   │               │
│  ┌──────▼───────────────────▼───────────┐  │
│  │       ROS2 Interface Layer           │  │
│  │  (rclpy native or rosbridge WS)      │  │
│  └──────────────────────────────────────┘  │
└────────────────────┬────────────────────────┘
                     │  DDS / Serial
┌────────────────────▼────────────────────────┐
│           ROS2 Robot System                 │
│  (Gazebo Sim / Nav2 / STM32 Firmware)       │
└─────────────────────────────────────────────┘
```

---

## 🧪 Running Tests

```bash
git clone https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server
cd ros2-mcp-server

python run_tests.py
```

All 13 unit tests run in **simulation mode** — no ROS2 installation required.

---

## 🗺️ Roadmap

- [x] Native `rclpy` interface with simulation fallback
- [x] `system_diagnostics`, `read_topic`, `publish_topic`, `tune_pid`, `set_parameter`
- [x] Three-tier execution sandbox with full audit logging
- [ ] `rosbridge_server` WebSocket transport for remote robot access
- [ ] Nav2 planner goal injection (`navigate_to_pose`)
- [ ] Gazebo Sim integration for zero-hardware testing
- [ ] ROS2 bag file replay tool (`replay_bag`)
- [ ] Multi-robot session support
- [ ] Web dashboard for live telemetry visualization

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server
pip install -e ".[dev]"
```

---

## 👨‍💻 Author

**Abdullah Bin Zafar** — Mechatronics & Control Engineering, UET Lahore  
Building robots that think and act.

[![GitHub](https://img.shields.io/badge/GitHub-EngineerAbdullahBinZafar-181717?style=for-the-badge&logo=github&logoColor=white&labelColor=0d1117)](https://github.com/EngineerAbdullahBinZafar)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin&logoColor=white&labelColor=0d1117)](https://linkedin.com/in/abdullah-bin-zafar)
[![Gmail](https://img.shields.io/badge/Gmail-Contact-EA4335?style=for-the-badge&logo=gmail&logoColor=white&labelColor=0d1117)](mailto:abz.king.1.9.2003@gmail.com)

---

## 💬 Community

- 🐛 Found a bug? [Open an issue](https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server/issues)
- 💡 Have an idea? [Start a discussion](https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server/discussions)
- ⭐ If this helped you, star the repo — it directly helps other robotics engineers find it.

---

<div align="center">
<img width="100%" src="https://capsule-render.vercel.app/api?type=rect&color=0:000033,50:0055ff,100:00d4ff&height=80&section=footer&text=Give+AI+Agents+a+Body&fontSize=22&fontColor=ffffff&fontAlignY=55&animation=fadeIn" />
</div>
