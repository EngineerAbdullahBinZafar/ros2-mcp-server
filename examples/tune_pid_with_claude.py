"""
Example: Interactive AI-Assisted PID Tuning Session

This script demonstrates an AI agent (running against simulation)
performing a step-by-step PID gain tuning session with diagnostics.
Run it with: python -m examples.tune_pid_with_claude
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ros2_mcp.ros2_interface import create_interface
from ros2_mcp.sandbox import CommandSandbox, SafetyLevel

def main():
    print("=" * 70)
    print("  ROS2-MCP: AI-Assisted PID Tuning Demo (Simulation Mode)")
    print("=" * 70)

    ros2 = create_interface()
    sandbox = CommandSandbox(SafetyLevel.FULL)  # Full for demo; use SAFE_WRITE on real robots

    from ros2_mcp.tools import handle_system_diagnostics, handle_get_pid_state, handle_tune_pid

    # Step 1: Run diagnostics
    print("\n[STEP 1] Running system diagnostics...")
    diag = handle_system_diagnostics(ros2)
    print(f"  System Status: {diag['system_status']}")
    for issue in diag.get('critical_issues', []):
        print(f"  [!] {issue}")
    for w in diag.get('warnings', []):
        print(f"  [~] {w}")
    for h in diag.get('healthy_checks', []):
        print(f"  [+] {h}")

    # Step 2: Read current PID gains
    print("\n[STEP 2] Reading PID gains from nav2_controller...")
    pid_state = handle_get_pid_state(ros2, "nav2_controller",
                                     kp_param="max_vel_x",
                                     ki_param="min_vel_x",
                                     kd_param="max_vel_theta")
    print(f"  Current gains: {pid_state['gains']}")

    # Step 3: AI applies tuning
    print("\n[STEP 3] AI agent applying tuning — reducing max_vel_x by 20%...")
    tune_result = handle_tune_pid(ros2, sandbox, "nav2_controller",
                                  kp=0.4,  # was 0.5
                                  kp_param="max_vel_x",
                                  ki_param="min_vel_x",
                                  kd_param="max_vel_theta")
    for res in tune_result.get('applied', []):
        print(f"  Applied: {res}")
    print(f"\n  AI Guidance: {tune_result['guidance']}")

    print("\n[DONE] PID tuning session complete.")
    print("In a real deployment, connect Claude or Antigravity to the MCP server")
    print("and ask: 'The drone pitch is oscillating — help me tune the PID gains.'")

if __name__ == "__main__":
    main()
