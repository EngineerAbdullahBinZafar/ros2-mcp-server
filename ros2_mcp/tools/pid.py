"""
MCP Tool: AI-Assisted PID Gain Tuning

Provides the AI agent with a structured interface to:
1. Read the current PID gains from a controller node.
2. Read the current error metric from a feedback topic.
3. Suggest and apply a gain adjustment.

This allows agents like Claude or Antigravity to perform closed-loop PID
tuning conversations, e.g.:
  "The attitude error is 4.2°. Try increasing Kp for the pitch axis from 2.0 to 2.4."
"""
from __future__ import annotations
from typing import Any, Dict, Optional


def handle_get_pid_state(ros2: Any, node_name: str,
                          kp_param: str = "kp",
                          ki_param: str = "ki",
                          kd_param: str = "kd") -> Dict:
    """Read current PID gains from a controller node."""
    kp = ros2.get_parameter(node_name, kp_param)
    ki = ros2.get_parameter(node_name, ki_param)
    kd = ros2.get_parameter(node_name, kd_param)
    return {
        "node": node_name,
        "gains": {
            "Kp": kp.get("value"),
            "Ki": ki.get("value"),
            "Kd": kd.get("value"),
        },
        "param_keys": {"Kp": kp_param, "Ki": ki_param, "Kd": kd_param}
    }


def handle_tune_pid(ros2: Any, sandbox: Any, node_name: str,
                    kp: Optional[float] = None,
                    ki: Optional[float] = None,
                    kd: Optional[float] = None,
                    kp_param: str = "kp",
                    ki_param: str = "ki",
                    kd_param: str = "kd") -> Dict:
    """Apply PID gain changes through the sandbox."""
    from .params import handle_set_parameter
    results = []
    if kp is not None:
        results.append(handle_set_parameter(ros2, sandbox, node_name, kp_param, float(kp)))
    if ki is not None:
        results.append(handle_set_parameter(ros2, sandbox, node_name, ki_param, float(ki)))
    if kd is not None:
        results.append(handle_set_parameter(ros2, sandbox, node_name, kd_param, float(kd)))
    if not results:
        return {"status": "error", "reason": "No gains provided. Specify at least one of: kp, ki, kd"}
    all_ok = all(r.get("status") == "ok" for r in results)
    return {
        "status": "ok" if all_ok else "partial",
        "applied": results,
        "guidance": (
            "Monitor the error topic for at least 3–5 seconds after each change. "
            "Increase Kp to reduce steady-state error. Increase Kd to dampen oscillation. "
            "Tune Ki last to eliminate residual bias."
        )
    }
