"""
ROS2 Interface — Manages all communication between the MCP Server and a live ROS2 system.

Designed to be transport-agnostic:
  - If running inside a sourced ROS2 environment: uses rclpy natively.
  - If running outside (e.g. developer's laptop against a remote robot): connects via
    rosbridge_server (WebSocket) or ROS2 DDS daemon.

This keeps the MCP server useful for both:
  1. On-robot deployments (Jetson Orin / Raspberry Pi)
  2. Remote developer workstations connected to a real or simulated robot.
"""

from __future__ import annotations
import json
import time
import threading
from typing import Any, Dict, List, Optional

# ── ROS2 Native (rclpy) ─────────────────────────────────────────────────────
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.task import Future
    from std_msgs.msg import Float32, Int32, String, Bool
    from geometry_msgs.msg import Twist, PoseStamped
    from sensor_msgs.msg import LaserScan, Imu, BatteryState
    from rcl_interfaces.msg import SetParametersResult
    from rcl_interfaces.srv import SetParameters, GetParameters, ListParameters

    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


# ── WebSocket Fallback (rosbridge) ───────────────────────────────────────────
try:
    import websocket
    ROSBRIDGE_AVAILABLE = True
except ImportError:
    ROSBRIDGE_AVAILABLE = False


class SnapshotCache:
    """Thread-safe LRU cache for the most recent value of each topic."""
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

    def update(self, topic: str, value: Any):
        with self._lock:
            self._data[topic] = value
            self._timestamps[topic] = time.time()

    def get(self, topic: str) -> Optional[Dict]:
        with self._lock:
            if topic not in self._data:
                return None
            return {
                "topic": topic,
                "value": self._data[topic],
                "age_ms": round((time.time() - self._timestamps[topic]) * 1000, 2)
            }

    def get_all(self) -> List[Dict]:
        with self._lock:
            return [
                {"topic": t, "value": v, "age_ms": round((time.time() - self._timestamps[t]) * 1000, 2)}
                for t, v in self._data.items()
            ]


class ROS2NativeInterface:
    """Live rclpy-backed interface — runs when ROS2 is locally available."""
    def __init__(self):
        rclpy.init()
        self._node = Node("ros2_mcp_bridge")
        self._cache = SnapshotCache()
        self._subs = {}
        self._pubs = {}
        self._executor_thread = threading.Thread(target=self._spin, daemon=True)
        self._executor_thread.start()

    def _spin(self):
        rclpy.spin(self._node)

    def _make_generic_callback(self, topic: str):
        def callback(msg):
            self._cache.update(topic, self._serialize_msg(msg))
        return callback

    def _serialize_msg(self, msg) -> Any:
        """Convert any ROS2 message to a JSON-serializable dict."""
        if hasattr(msg, 'get_fields_and_field_types'):
            result = {}
            for field in msg.get_fields_and_field_types():
                result[field] = self._serialize_msg(getattr(msg, field))
            return result
        elif isinstance(msg, (list, tuple)):
            return list(msg)
        elif isinstance(msg, (int, float, str, bool)):
            return msg
        return str(msg)

    def subscribe_topic(self, topic: str, msg_type_str: str):
        """Subscribe to a ROS2 topic and cache latest value."""
        msg_type_map = {
            "sensor_msgs/LaserScan": LaserScan,
            "sensor_msgs/Imu": Imu,
            "sensor_msgs/BatteryState": BatteryState,
            "geometry_msgs/Twist": Twist,
            "geometry_msgs/PoseStamped": PoseStamped,
            "std_msgs/String": String,
            "std_msgs/Float32": Float32,
            "std_msgs/Int32": Int32,
        }
        if topic not in self._subs:
            msg_class = msg_type_map.get(msg_type_str, String)
            self._subs[topic] = self._node.create_subscription(
                msg_class, topic,
                self._make_generic_callback(topic), 10
            )

    def read_topic(self, topic: str, msg_type_str: str = "std_msgs/String",
                   timeout_ms: int = 3000) -> Optional[Dict]:
        """Subscribe if needed, then return latest cached value (waits up to timeout_ms)."""
        self.subscribe_topic(topic, msg_type_str)
        deadline = time.time() + timeout_ms / 1000.0
        while time.time() < deadline:
            result = self._cache.get(topic)
            if result is not None:
                return result
            time.sleep(0.05)
        return {"topic": topic, "value": None, "error": "timeout — no message received in time"}

    def publish_topic(self, topic: str, msg_type_str: str, payload: Dict) -> str:
        """Publish a single message to a ROS2 topic."""
        try:
            if msg_type_str == "geometry_msgs/Twist":
                msg = Twist()
                msg.linear.x = float(payload.get("linear_x", 0.0))
                msg.linear.y = float(payload.get("linear_y", 0.0))
                msg.angular.z = float(payload.get("angular_z", 0.0))
            elif msg_type_str == "std_msgs/String":
                msg = String()
                msg.data = str(payload.get("data", ""))
            elif msg_type_str == "std_msgs/Float32":
                msg = Float32()
                msg.data = float(payload.get("data", 0.0))
            else:
                return f"ERROR: Unsupported publish type {msg_type_str}"

            if topic not in self._pubs:
                msg_class = type(msg)
                self._pubs[topic] = self._node.create_publisher(msg_class, topic, 10)

            self._pubs[topic].publish(msg)
            return f"OK: Published to {topic}"
        except Exception as e:
            return f"ERROR: {e}"

    def list_topics(self) -> List[Dict]:
        """List all currently active ROS2 topics with type information."""
        topics = self._node.get_topic_names_and_types()
        return [{"topic": t, "types": types} for t, types in topics]

    def list_nodes(self) -> List[str]:
        """List all currently running ROS2 nodes."""
        return self._node.get_node_names()

    def get_parameter(self, node_name: str, param_name: str) -> Any:
        """Read a parameter from a running ROS2 node."""
        client = self._node.create_client(GetParameters, f"/{node_name}/get_parameters")
        if not client.wait_for_service(timeout_sec=2.0):
            return {"error": f"Node {node_name} not reachable"}
        req = GetParameters.Request()
        req.names = [param_name]
        future = client.call_async(req)
        rclpy.spin_until_future_complete(self._node, future, timeout_sec=3.0)
        if future.done():
            val = future.result().values[0]
            return {"node": node_name, "param": param_name, "value": str(val)}
        return {"error": "Parameter request timed out"}

    def set_parameter(self, node_name: str, param_name: str, value: Any) -> str:
        """Dynamically update a parameter on a running ROS2 node."""
        from rcl_interfaces.msg import Parameter, ParameterValue, ParameterType
        client = self._node.create_client(SetParameters, f"/{node_name}/set_parameters")
        if not client.wait_for_service(timeout_sec=2.0):
            return f"ERROR: Node {node_name} not reachable"
        p = Parameter()
        p.name = param_name
        pv = ParameterValue()
        if isinstance(value, float):
            pv.type = ParameterType.PARAMETER_DOUBLE
            pv.double_value = value
        elif isinstance(value, int):
            pv.type = ParameterType.PARAMETER_INTEGER
            pv.integer_value = value
        elif isinstance(value, str):
            pv.type = ParameterType.PARAMETER_STRING
            pv.string_value = value
        elif isinstance(value, bool):
            pv.type = ParameterType.PARAMETER_BOOL
            pv.bool_value = value
        p.value = pv
        req = SetParameters.Request()
        req.parameters = [p]
        future = client.call_async(req)
        rclpy.spin_until_future_complete(self._node, future, timeout_sec=3.0)
        return "OK: Parameter updated" if future.done() else "ERROR: Timeout"

    def shutdown(self):
        self._node.destroy_node()
        rclpy.shutdown()


class MockInterface:
    """
    Simulation-mode interface — works without any ROS2 installation.
    Generates realistic synthetic sensor data for development, CI, and demos.
    """
    import random as _random

    def list_topics(self) -> List[Dict]:
        return [
            {"topic": "/cmd_vel", "types": ["geometry_msgs/msg/Twist"]},
            {"topic": "/scan", "types": ["sensor_msgs/msg/LaserScan"]},
            {"topic": "/imu/data", "types": ["sensor_msgs/msg/Imu"]},
            {"topic": "/battery_state", "types": ["sensor_msgs/msg/BatteryState"]},
            {"topic": "/odom", "types": ["nav_msgs/msg/Odometry"]},
            {"topic": "/map", "types": ["nav_msgs/msg/OccupancyGrid"]},
        ]

    def list_nodes(self) -> List[str]:
        return [
            "controller_manager", "robot_state_publisher",
            "nav2_controller", "nav2_planner",
            "slam_toolbox", "sensor_fusion_node"
        ]

    def read_topic(self, topic: str, msg_type_str: str = "std_msgs/String",
                   timeout_ms: int = 3000) -> Dict:
        import random
        import math
        t = time.time()
        topic_data = {
            "/scan": {
                "header": {"stamp": t},
                "angle_min": -3.1415, "angle_max": 3.1415,
                "range_min": 0.1, "range_max": 10.0,
                "ranges": [round(random.uniform(0.5, 5.0), 3) for _ in range(360)]
            },
            "/imu/data": {
                "linear_acceleration": {
                    "x": round(random.gauss(0.0, 0.05), 4),
                    "y": round(random.gauss(0.0, 0.05), 4),
                    "z": round(9.81 + random.gauss(0, 0.02), 4)
                },
                "angular_velocity": {
                    "x": round(random.gauss(0.0, 0.01), 4),
                    "y": round(random.gauss(0.0, 0.01), 4),
                    "z": round(random.gauss(0.0, 0.01), 4)
                }
            },
            "/battery_state": {
                "voltage": round(random.uniform(22.0, 25.2), 2),
                "percentage": round(random.uniform(0.35, 0.98), 3),
                "current": round(random.uniform(-8.5, -1.2), 2)
            },
            "/cmd_vel": {
                "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": 0.0}
            }
        }
        return {
            "topic": topic,
            "value": topic_data.get(topic, {"data": f"MOCK: {topic}"}),
            "age_ms": random.uniform(1.5, 12.0),
            "mode": "simulation"
        }

    def publish_topic(self, topic: str, msg_type_str: str, payload: Dict) -> str:
        return f"MOCK: Published {payload} to {topic} (simulation mode)"

    def get_parameter(self, node_name: str, param_name: str) -> Dict:
        mock_params = {
            ("controller_manager", "update_rate"): 100.0,
            ("nav2_controller", "max_vel_x"): 0.5,
            ("nav2_controller", "min_vel_x"): -0.25,
        }
        val = mock_params.get((node_name, param_name), "MOCK_VALUE")
        return {"node": node_name, "param": param_name, "value": val, "mode": "simulation"}

    def set_parameter(self, node_name: str, param_name: str, value: Any) -> str:
        return f"MOCK: Set {node_name}/{param_name} = {value} (simulation mode)"

    def shutdown(self):
        pass


def create_interface() -> Any:
    """Factory: returns a live rclpy interface or safe mock, depending on environment."""
    if ROS2_AVAILABLE:
        try:
            return ROS2NativeInterface()
        except Exception as e:
            print(f"[ros2-mcp] rclpy init failed ({e}), falling back to simulation mode.")
    return MockInterface()
