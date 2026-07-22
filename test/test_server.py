import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ros2_mcp.sandbox import CommandSandbox, SafetyLevel, SandboxBlockedError

def test_sandbox_read_only_blocks_publish():
    sandbox = CommandSandbox(SafetyLevel.READ_ONLY)
    try:
        sandbox.check_publish("/cmd_vel", {"linear_x": 0.5})
        assert False, "Should have raised SandboxBlockedError"
    except SandboxBlockedError as e:
        assert "READ_ONLY" in str(e)

def test_sandbox_safe_write_allows_allowlisted_topic():
    sandbox = CommandSandbox(SafetyLevel.SAFE_WRITE)
    result = sandbox.check_publish("/cmd_vel", {"linear_x": 0.5})
    assert result is True

def test_sandbox_safe_write_blocks_unknown_topic():
    sandbox = CommandSandbox(SafetyLevel.SAFE_WRITE)
    try:
        sandbox.check_publish("/destructive_actuator", {"fire": True})
        assert False, "Should have raised SandboxBlockedError"
    except SandboxBlockedError as e:
        assert "not in the safe-write allow-list" in str(e)

def test_sandbox_full_mode_allows_any_topic():
    sandbox = CommandSandbox(SafetyLevel.FULL)
    result = sandbox.check_publish("/any_dangerous_topic", {"data": "test"})
    assert result is True

def test_sandbox_audit_log():
    sandbox = CommandSandbox(SafetyLevel.FULL)
    sandbox.check_publish("/cmd_vel", {})
    log = sandbox.get_audit_log()
    assert len(log) == 1
    assert log[0]["allowed"] is True
    assert log[0]["action"] == "publish"

def test_sandbox_allow_topic_dynamic():
    sandbox = CommandSandbox(SafetyLevel.SAFE_WRITE)
    try:
        sandbox.check_publish("/custom_motor", {})
        assert False
    except SandboxBlockedError:
        pass
    sandbox.allow_topic("/custom_motor")
    result = sandbox.check_publish("/custom_motor", {})
    assert result is True

from ros2_mcp.ros2_interface import MockInterface

def test_mock_interface_list_topics():
    iface = MockInterface()
    topics = iface.list_topics()
    assert len(topics) >= 5
    topic_names = [t["topic"] for t in topics]
    assert "/scan" in topic_names
    assert "/imu/data" in topic_names

def test_mock_interface_read_scan():
    iface = MockInterface()
    result = iface.read_topic("/scan", "sensor_msgs/LaserScan")
    val = result["value"]
    assert "ranges" in val
    assert len(val["ranges"]) == 360
    for r in val["ranges"]:
        assert 0.5 <= r <= 5.0

def test_mock_interface_read_battery():
    iface = MockInterface()
    result = iface.read_topic("/battery_state", "sensor_msgs/BatteryState")
    val = result["value"]
    assert "voltage" in val
    assert 22.0 <= val["voltage"] <= 25.2

def test_mock_interface_publish():
    iface = MockInterface()
    result = iface.publish_topic("/cmd_vel", "geometry_msgs/Twist", {"linear_x": 0.3})
    assert "MOCK" in result

from ros2_mcp.tools.diagnostics import handle_system_diagnostics

def test_diagnostics_returns_status():
    iface = MockInterface()
    result = handle_system_diagnostics(iface)
    assert "system_status" in result
    assert result["system_status"] in ("HEALTHY", "WARNING", "CRITICAL")
    assert "healthy_checks" in result
    assert "active_nodes" in result

from ros2_mcp.tools.topics import handle_list_topics, handle_read_topic

def test_list_topics():
    iface = MockInterface()
    result = handle_list_topics(iface)
    assert "total" in result
    assert result["total"] >= 5

def test_read_topic_normalizes_slash():
    iface = MockInterface()
    result = handle_read_topic(iface, "scan", "sensor_msgs/LaserScan")
    assert result["topic"] == "/scan"
