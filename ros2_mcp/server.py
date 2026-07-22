"""
ROS2 MCP Server — Core Server

Implements the Model Context Protocol (MCP) stdio transport spec.
Registers and dispatches all ROS2 tools to AI agents.

Supports any MCP-compatible client:
  - Claude Desktop (via MCP plugin)
  - Antigravity IDE (via mcp: tool calls)
  - OpenAI Agents SDK
  - Any custom client using stdio JSON-RPC 2.0
"""

from __future__ import annotations
import sys
import json
import traceback
import os
from typing import Any, Dict, Optional

from .ros2_interface import create_interface
from .sandbox import CommandSandbox, SafetyLevel
from .tools import (
    handle_list_topics, handle_read_topic, handle_publish_topic, handle_get_robot_snapshot,
    handle_list_nodes, handle_get_node_info,
    handle_get_parameter, handle_set_parameter,
    handle_get_pid_state, handle_tune_pid,
    handle_system_diagnostics,
)

SERVER_INFO = {
    "name": "ros2-mcp-server",
    "version": "1.0.0",
    "description": "Connect Claude, Antigravity, and any AI agent to real ROS2 robots.",
    "author": "Abdullah Bin Zafar (EngineerAbdullahBinZafar)",
    "repository": "https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server",
    "capabilities": {
        "tools": True,
        "resources": False,
        "prompts": False,
        "logging": True,
    }
}

TOOL_SCHEMAS = [
    {
        "name": "system_diagnostics",
        "description": (
            "Run a full robot health check. Returns battery level, LiDAR status, "
            "IMU health, active node count, and a list of critical issues/warnings. "
            "ALWAYS call this first when the user asks 'what's wrong?' or 'is the robot ready?'"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_topics",
        "description": "List all active ROS2 topics and their message types on the connected robot.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "read_topic",
        "description": (
            "Read the latest message from a ROS2 topic. Returns the full serialized message "
            "and the age of the data in milliseconds. Use for inspecting sensor readings, "
            "odometry, battery state, etc."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The full topic name (e.g. '/scan', '/imu/data', '/battery_state')"
                },
                "msg_type": {
                    "type": "string",
                    "description": "The ROS2 message type (e.g. 'sensor_msgs/LaserScan')",
                    "default": "std_msgs/String"
                },
                "timeout_ms": {
                    "type": "integer",
                    "description": "Maximum wait time for a message in milliseconds",
                    "default": 3000
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "publish_topic",
        "description": (
            "Publish a message to a ROS2 topic. Subject to sandbox safety checks — "
            "blocked in READ_ONLY mode and restricted to the allowlist in SAFE_WRITE mode. "
            "Use to send velocity commands, LED state, arm target angle, etc."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to publish to (e.g. '/cmd_vel')"
                },
                "msg_type": {
                    "type": "string",
                    "description": "Message type (e.g. 'geometry_msgs/Twist')"
                },
                "payload": {
                    "type": "object",
                    "description": "The message payload as a key-value dictionary"
                }
            },
            "required": ["topic", "msg_type", "payload"]
        }
    },
    {
        "name": "get_robot_snapshot",
        "description": (
            "Fetch a comprehensive multi-topic snapshot covering LiDAR, IMU, "
            "battery state, and odometry in a single efficient call."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_nodes",
        "description": "List all currently running ROS2 nodes on the connected robot.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_node_info",
        "description": "Inspect a specific ROS2 node and find its related topics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_name": {"type": "string", "description": "Name of the ROS2 node to inspect"}
            },
            "required": ["node_name"]
        }
    },
    {
        "name": "get_parameter",
        "description": "Read a live parameter from a running ROS2 node (e.g. PID gains, velocity limits).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_name": {"type": "string"},
                "param_name": {"type": "string"}
            },
            "required": ["node_name", "param_name"]
        }
    },
    {
        "name": "set_parameter",
        "description": (
            "Dynamically update a parameter on a running ROS2 node. "
            "Sandboxed — only allowed parameters can be modified in SAFE_WRITE mode."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_name": {"type": "string"},
                "param_name": {"type": "string"},
                "value": {"description": "New parameter value (float, int, string, or bool)"}
            },
            "required": ["node_name", "param_name", "value"]
        }
    },
    {
        "name": "get_pid_state",
        "description": "Read the current Kp, Ki, Kd gains from a PID controller node.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_name": {"type": "string", "description": "Controller node name"},
                "kp_param": {"type": "string", "default": "kp"},
                "ki_param": {"type": "string", "default": "ki"},
                "kd_param": {"type": "string", "default": "kd"}
            },
            "required": ["node_name"]
        }
    },
    {
        "name": "tune_pid",
        "description": (
            "Apply new PID gains to a controller node. "
            "Provide the new Kp, Ki, and/or Kd values. "
            "Returns tuning guidance based on the engineering methodology."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_name": {"type": "string"},
                "kp": {"type": "number", "description": "New proportional gain"},
                "ki": {"type": "number", "description": "New integral gain"},
                "kd": {"type": "number", "description": "New derivative gain"},
                "kp_param": {"type": "string", "default": "kp"},
                "ki_param": {"type": "string", "default": "ki"},
                "kd_param": {"type": "string", "default": "kd"}
            },
            "required": ["node_name"]
        }
    }
]


class ROS2MCPServer:
    def __init__(self):
        safety_level_str = os.environ.get("SAFETY_LEVEL", "safe_write").lower()
        try:
            safety_level = SafetyLevel(safety_level_str)
        except ValueError:
            safety_level = SafetyLevel.SAFE_WRITE

        self.ros2 = create_interface()
        self.sandbox = CommandSandbox(level=safety_level)
        self._log(f"ROS2 MCP Server v{SERVER_INFO['version']} started | Safety: {safety_level.value}")

    def _log(self, msg: str):
        print(f"[ros2-mcp] {msg}", file=sys.stderr, flush=True)

    def _send(self, obj: Dict):
        print(json.dumps(obj), flush=True)

    def _error(self, req_id: Any, code: int, message: str) -> Dict:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def _call_tool(self, name: str, args: Dict) -> Any:
        if name == "system_diagnostics":
            return handle_system_diagnostics(self.ros2)
        elif name == "list_topics":
            return handle_list_topics(self.ros2)
        elif name == "read_topic":
            return handle_read_topic(self.ros2, args["topic"],
                                     args.get("msg_type", "std_msgs/String"),
                                     args.get("timeout_ms", 3000))
        elif name == "publish_topic":
            return handle_publish_topic(self.ros2, self.sandbox,
                                        args["topic"], args["msg_type"], args["payload"])
        elif name == "get_robot_snapshot":
            return handle_get_robot_snapshot(self.ros2)
        elif name == "list_nodes":
            return handle_list_nodes(self.ros2)
        elif name == "get_node_info":
            return handle_get_node_info(self.ros2, args["node_name"])
        elif name == "get_parameter":
            return handle_get_parameter(self.ros2, args["node_name"], args["param_name"])
        elif name == "set_parameter":
            return handle_set_parameter(self.ros2, self.sandbox,
                                        args["node_name"], args["param_name"], args["value"])
        elif name == "get_pid_state":
            return handle_get_pid_state(self.ros2, args["node_name"],
                                        args.get("kp_param", "kp"),
                                        args.get("ki_param", "ki"),
                                        args.get("kd_param", "kd"))
        elif name == "tune_pid":
            return handle_tune_pid(self.ros2, self.sandbox, args["node_name"],
                                   args.get("kp"), args.get("ki"), args.get("kd"),
                                   args.get("kp_param", "kp"),
                                   args.get("ki_param", "ki"),
                                   args.get("kd_param", "kd"))
        else:
            raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, req: Dict) -> Optional[Dict]:
        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": SERVER_INFO,
                    "capabilities": SERVER_INFO["capabilities"]
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"tools": TOOL_SCHEMAS}
            }

        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            try:
                result = self._call_tool(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                        "isError": False
                    }
                }
            except Exception as e:
                tb = traceback.format_exc()
                self._log(f"Tool error [{tool_name}]: {e}\n{tb}")
                return {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {e}"}],
                        "isError": True
                    }
                }

        elif method == "notifications/initialized":
            return None  # No response needed for notifications

        else:
            return self._error(req_id, -32601, f"Method not found: {method}")

    def run(self):
        self._log("Ready. Waiting for MCP requests on stdin...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                response = self.handle_request(req)
                if response is not None:
                    self._send(response)
            except json.JSONDecodeError as e:
                self._log(f"Invalid JSON: {e}")
                self._send(self._error(None, -32700, "Parse error"))
            except Exception as e:
                self._log(f"Unhandled exception: {e}\n{traceback.format_exc()}")

        self._log("stdin closed, shutting down.")
        self.ros2.shutdown()


def main():
    server = ROS2MCPServer()
    server.run()


if __name__ == "__main__":
    main()
