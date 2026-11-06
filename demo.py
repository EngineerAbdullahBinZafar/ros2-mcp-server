#!/usr/bin/env python3
"""
ROS 2 MCP Server — Live 1-Second Terminal Demonstration
Zero-dependency simulation of Model Context Protocol (MCP) tools for ROS 2,
demonstrating 3-tier safety sandbox, telemetry inspection, and predictive safety.

Usage:
    python demo.py
"""

import os
import sys
import time

# Ensure local package is in import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ros2_mcp.ros2_interface import MockInterface
from ros2_mcp.sandbox import CommandSandbox, SafetyLevel, SandboxBlockedError
from ros2_mcp.tools.diagnostics import handle_system_diagnostics
from ros2_mcp.tools.topics import handle_get_robot_snapshot, handle_list_topics


def run_demo():
    print("=" * 70)
    print("  ROS 2 MCP SERVER — AI AGENTIC ROBOTICS GATEWAY DEMO")
    print("  Model Context Protocol (MCP) · 3-Tier Security Sandbox · Mock ROS 2")
    print("=" * 70)

    # 1. Initialize Mock ROS 2 Interface & Security Sandbox
    mock_if = MockInterface()
    sandbox = CommandSandbox(SafetyLevel.SAFE_WRITE)

    print("\n[Step 1] Inspecting Live ROS 2 Node Topology & Topics (Simulated)...")
    topics = mock_if.list_topics()
    nodes = mock_if.list_nodes()
    print(f"  Active Topics ({len(topics)}): {', '.join(t['topic'] for t in topics[:4])}...")
    print(f"  Active Nodes  ({len(nodes)}): {', '.join(n[0] for n in nodes[:3])}...")

    # 2. Real-Time Telemetry & Diagnostics Inspection
    print("\n[Step 2] Executing 'system_diagnostics' MCP Tool...")
    diag_result = handle_system_diagnostics(mock_if)
    scan_data = mock_if.read_topic("/scan")
    battery_data = mock_if.read_topic("/battery_state")
    imu_data = mock_if.read_topic("/imu/data")

    min_range = min(scan_data.get("ranges", [1.0]))
    batt_pct = battery_data.get("percentage", 100.0)
    print(f"  * Battery Level   : {batt_pct:.1f}% [NOMINAL]")
    print(f"  * Nearest Obstacle: {min_range:.2f} m (Forward Sector)")
    print(f"  * Diagnostics Tool: Status='{diag_result.get('status', 'OK')}'")

    # 3. 3-Tier Security Sandbox Verification
    print("\n[Step 3] Verifying 3-Tier Command Sandbox Guardrails...")
    print("  Active Sandbox Level: 'safe_write' (Allowlisted topics: /cmd_vel, /target_velocity)")

    # Safe write test
    try:
        sandbox.check_publish("/cmd_vel", {"linear": {"x": 0.5}})
        print("  --> Publish to '/cmd_vel' : \033[92mALLOWED\033[0m (Standard navigation topic)")
    except SandboxBlockedError as e:
        print(f"  --> Publish to '/cmd_vel' : BLOCKED ({e})")

    # Unsafe unauthorized write test
    try:
        sandbox.check_publish("/actuator_raw_pwm", {"pwm": 255})
        print("  --> Publish to '/actuator_raw_pwm' : ALLOWED")
    except SandboxBlockedError as e:
        print("  --> Publish to '/actuator_raw_pwm' : \033[91mBLOCKED\033[0m [Sandbox Violation Safely Prevented!]")

    # Read-only test
    ro_sandbox = CommandSandbox(SafetyLevel.READ_ONLY)
    try:
        ro_sandbox.check_publish("/cmd_vel", {"linear": {"x": 0.5}})
    except SandboxBlockedError as e:
        print(f"  --> Under 'read_only' mode : \033[91mALL WRITES REJECTED\033[0m")

    # 4. Summary & Capabilities
    print("\n" + "-" * 70)
    print("MCP SERVER SPECIFICATION & PROTOCOL COMPLIANCE:")
    print("  * Specification : Anthropic Model Context Protocol (MCP) JSON-RPC 2.0")
    print("  * Target Stack  : ROS 2 Humble / Iron / Jazzy & Native micro-ROS")
    print("  * Built-in Tools: list_topics, read_topic, publish_topic, system_diagnostics,")
    print("                    get_spatial_map, predict_trajectory, tune_pid, swarm_status")
    print("  * Safety Sandbox: 3-tier stateful permission gate (read_only, safe_write, full)")
    print("-" * 70)
    print("RESULT: ROS 2 MCP Server Ready. Agents can safely inspect and control robots.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_demo()
