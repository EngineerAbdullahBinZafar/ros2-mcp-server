"""
MCP Tool: Robot Diagnostics

Provides a single comprehensive system health snapshot for the AI agent,
summarizing battery state, sensor liveness, and dangerous conditions in one call.
"""
from __future__ import annotations
from typing import Any, Dict, List


def handle_system_diagnostics(ros2: Any) -> Dict:
    """
    Returns a rich health report of the robot system.
    Designed to be the FIRST tool the AI agent calls when asked
    'What's wrong with the robot?' or 'Is the robot ready?'
    """
    issues = []
    warnings = []
    healthy = []

    # 1. Check battery
    batt = ros2.read_topic("/battery_state", "sensor_msgs/BatteryState", timeout_ms=500)
    batt_val = batt.get("value", {})
    voltage = batt_val.get("voltage", None)
    pct = batt_val.get("percentage", None)
    if voltage is not None:
        if pct is not None and pct < 0.20:
            issues.append(f"CRITICAL: Battery at {pct*100:.0f}% ({voltage:.1f}V) — return to base immediately")
        elif pct is not None and pct < 0.35:
            warnings.append(f"WARNING: Battery at {pct*100:.0f}% ({voltage:.1f}V) — consider recharging")
        else:
            healthy.append(f"Battery: {pct*100:.0f}% ({voltage:.1f}V)")
    else:
        warnings.append("WARNING: /battery_state not reachable — power status unknown")

    # 2. Check LiDAR scan
    scan = ros2.read_topic("/scan", "sensor_msgs/LaserScan", timeout_ms=500)
    scan_val = scan.get("value", {})
    ranges = scan_val.get("ranges", [])
    if ranges:
        import math
        valid = [r for r in ranges if not math.isnan(r) and not math.isinf(r)]
        min_dist = min(valid) if valid else 0.0
        if min_dist < 0.30:
            issues.append(f"CRITICAL: Obstacle at {min_dist:.2f}m — collision imminent")
        elif min_dist < 0.75:
            warnings.append(f"WARNING: Close obstacle at {min_dist:.2f}m")
        else:
            healthy.append(f"LiDAR: {len(valid)} valid rays, closest object at {min_dist:.2f}m")
    else:
        warnings.append("WARNING: /scan topic returned empty data — LiDAR may be offline")

    # 3. Check IMU
    imu = ros2.read_topic("/imu/data", "sensor_msgs/Imu", timeout_ms=500)
    imu_val = imu.get("value", {})
    accel = imu_val.get("linear_acceleration", {})
    az = accel.get("z", None)
    if az is not None:
        if abs(az - 9.81) > 3.0:
            issues.append(f"CRITICAL: IMU Z-acceleration anomaly ({az:.2f} m/s²) — check tilt/vibration")
        else:
            healthy.append(f"IMU: Z-accel {az:.2f} m/s² (nominal)")
    else:
        warnings.append("WARNING: /imu/data not available — attitude estimation degraded")

    # 4. Node count
    nodes = ros2.list_nodes()
    healthy.append(f"Active nodes: {len(nodes)} running")

    overall = "CRITICAL" if issues else ("WARNING" if warnings else "HEALTHY")

    return {
        "system_status": overall,
        "critical_issues": issues,
        "warnings": warnings,
        "healthy_checks": healthy,
        "active_nodes": len(nodes),
        "recommendation": (
            "Address CRITICAL issues before motion. "
            "Use read_topic and tune_pid for detailed investigation."
        ) if issues or warnings else "Robot appears ready for operation."
    }
