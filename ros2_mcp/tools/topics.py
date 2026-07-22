"""MCP Tools for ROS2 Topics — list, read, and publish."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..sandbox import SandboxBlockedError


def handle_list_topics(ros2: Any) -> Dict:
    topics = ros2.list_topics()
    return {
        "total": len(topics),
        "topics": topics
    }


def handle_read_topic(ros2: Any, topic: str, msg_type: str, timeout_ms: int = 3000) -> Dict:
    if not topic.startswith("/"):
        topic = "/" + topic
    result = ros2.read_topic(topic, msg_type, timeout_ms)
    return result


def handle_publish_topic(ros2: Any, sandbox: Any, topic: str, msg_type: str, payload: Dict) -> Dict:
    if not topic.startswith("/"):
        topic = "/" + topic
    try:
        sandbox.check_publish(topic, payload)
        result = ros2.publish_topic(topic, msg_type, payload)
        return {"status": "ok", "result": result}
    except SandboxBlockedError as e:
        return {"status": "blocked", "reason": str(e)}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def handle_get_robot_snapshot(ros2: Any) -> Dict:
    """Fetch the most diagnostically useful topics in a single shot."""
    key_topics = [
        ("/scan", "sensor_msgs/LaserScan"),
        ("/imu/data", "sensor_msgs/Imu"),
        ("/battery_state", "sensor_msgs/BatteryState"),
        ("/cmd_vel", "geometry_msgs/Twist"),
        ("/odom", "nav_msgs/Odometry"),
    ]
    snapshot = {}
    for topic, msg_type in key_topics:
        try:
            result = ros2.read_topic(topic, msg_type, timeout_ms=500)
            snapshot[topic] = result
        except Exception as e:
            snapshot[topic] = {"error": str(e)}
    return {"snapshot": snapshot, "topic_count": len(key_topics)}
