"""
Execution Sandbox — Prevents AI agents from executing destructive commands
on the real robot without explicit allowlisting.

Safety Levels:
  READ_ONLY   → AI can only read topics and node state, cannot publish.
  SAFE_WRITE  → AI can publish to pre-approved topics (e.g. /cmd_vel) only.
  FULL        → AI has unrestricted publish/parameter-write access.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class SafetyLevel(str, Enum):
    READ_ONLY = "read_only"
    SAFE_WRITE = "safe_write"
    FULL = "full"


# Default allow-list for SAFE_WRITE mode.
# Add or remove topics and nodes for your specific robot platform.
DEFAULT_SAFE_TOPICS = {
    "/cmd_vel",
    "/target_velocity",
    "/led_state",
    "/speaker_cmd",
    "/arm_target_angle",
}

DEFAULT_SAFE_NODES = {
    "controller_manager",
    "nav2_controller",
    "nav2_planner",
    "robot_state_publisher",
}

DEFAULT_SAFE_PARAMS = {
    ("nav2_controller", "max_vel_x"),
    ("nav2_controller", "max_vel_theta"),
    ("nav2_controller", "min_vel_x"),
}


class CommandSandbox:
    """
    Validates every AI-requested action before it reaches hardware.
    
    Usage:
        sandbox = CommandSandbox(SafetyLevel.SAFE_WRITE)
        sandbox.check_publish("/cmd_vel", payload)   # raises if blocked
    """
    def __init__(
        self,
        level: SafetyLevel = SafetyLevel.SAFE_WRITE,
        allowed_topics: Optional[set] = None,
        allowed_nodes: Optional[set] = None,
        allowed_params: Optional[set] = None,
    ):
        self.level = level
        self.allowed_topics = allowed_topics or DEFAULT_SAFE_TOPICS.copy()
        self.allowed_nodes = allowed_nodes or DEFAULT_SAFE_NODES.copy()
        self.allowed_params = allowed_params or DEFAULT_SAFE_PARAMS.copy()
        self._audit_log: List[Dict] = []

    def _log(self, action: str, target: str, allowed: bool, reason: str = ""):
        import time
        self._audit_log.append({
            "timestamp": round(time.time(), 3),
            "action": action,
            "target": target,
            "allowed": allowed,
            "reason": reason,
            "safety_level": self.level.value
        })

    def check_publish(self, topic: str, payload: Any) -> bool:
        """Returns True if publish is allowed; raises SandboxBlockedError if blocked."""
        if self.level == SafetyLevel.FULL:
            self._log("publish", topic, True, "FULL mode")
            return True
        if self.level == SafetyLevel.READ_ONLY:
            self._log("publish", topic, False, "READ_ONLY mode — all writes blocked")
            raise SandboxBlockedError(
                f"BLOCKED: Publish to '{topic}' refused — server running in READ_ONLY mode.\n"
                "Set SAFETY_LEVEL=safe_write or SAFETY_LEVEL=full to allow writes."
            )
        # SAFE_WRITE: check topic allow-list
        if topic not in self.allowed_topics:
            self._log("publish", topic, False, "topic not in allowlist")
            raise SandboxBlockedError(
                f"BLOCKED: Topic '{topic}' is not in the safe-write allow-list.\n"
                f"Allowed topics: {sorted(self.allowed_topics)}\n"
                "To add it, call: sandbox.allow_topic(topic)"
            )
        self._log("publish", topic, True, "topic in allowlist")
        return True

    def check_set_parameter(self, node_name: str, param_name: str) -> bool:
        """Returns True if parameter write is allowed."""
        if self.level == SafetyLevel.FULL:
            self._log("set_param", f"{node_name}/{param_name}", True, "FULL mode")
            return True
        if self.level == SafetyLevel.READ_ONLY:
            self._log("set_param", f"{node_name}/{param_name}", False, "READ_ONLY mode")
            raise SandboxBlockedError(
                f"BLOCKED: set_parameter on '{node_name}/{param_name}' refused — READ_ONLY mode."
            )
        if (node_name, param_name) not in self.allowed_params:
            self._log("set_param", f"{node_name}/{param_name}", False, "param not in allowlist")
            raise SandboxBlockedError(
                f"BLOCKED: Parameter '{node_name}/{param_name}' is not in the safe-write allowlist.\n"
                f"Allowed: {sorted(self.allowed_params)}"
            )
        self._log("set_param", f"{node_name}/{param_name}", True, "param in allowlist")
        return True

    def allow_topic(self, topic: str):
        """Dynamically add a topic to the safe-write allowlist."""
        self.allowed_topics.add(topic)

    def allow_param(self, node_name: str, param_name: str):
        """Dynamically add a parameter to the safe-write allowlist."""
        self.allowed_params.add((node_name, param_name))

    def get_audit_log(self) -> List[Dict]:
        """Return the complete audit log of all decisions."""
        return list(self._audit_log)

    def clear_audit_log(self):
        self._audit_log.clear()


class SandboxBlockedError(Exception):
    """Raised when an AI agent attempts an action blocked by the sandbox."""
    pass
