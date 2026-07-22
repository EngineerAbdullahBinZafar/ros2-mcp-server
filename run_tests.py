"""
ros2-mcp-server v1.1.0 — Test Runner
Discovers and runs all tests in simulation mode (zero ROS2 install required).
"""

import sys
import os
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tests.test_server import (
    # Sandbox tests
    test_sandbox_read_only_blocks_publish,
    test_sandbox_safe_write_allows_allowlisted,
    test_sandbox_safe_write_blocks_unknown,
    test_sandbox_full_allows_any,
    test_sandbox_audit_log_thread_safe,
    test_sandbox_dynamic_allow_topic,
    test_sandbox_audit_summary,
    test_sandbox_read_only_blocks_set_parameter,
    # Mock interface tests
    test_mock_list_topics_has_required_topics,
    test_mock_list_nodes_returns_tuples,
    test_mock_read_scan_realistic,
    test_mock_read_battery_all_fields,
    test_mock_read_imu_has_orientation,
    test_mock_ping,
    test_mock_latched_topic,
    test_mock_publish_returns_string,
    # Diagnostics tests
    test_diagnostics_returns_valid_structure,
    test_diagnostics_sensor_fault_not_collision,
    test_diagnostics_battery_pct_none_no_crash,
    # Topics tools tests
    test_list_topics_total,
    test_read_topic_slash_normalization,
    test_read_topic_latched_flag,
    test_get_robot_snapshot_parallel,
    # Nodes tools tests
    test_list_nodes_structure,
    test_get_node_info_found,
    test_get_node_info_not_found,
    test_get_node_info_case_sensitive,
    # PID tools tests
    test_get_pid_state_returns_gains,
    test_tune_pid_rejects_negative_kp,
    test_tune_pid_rejects_extreme_value,
    test_tune_pid_valid_gains_apply,
    test_tune_pid_no_gains_provided,
    test_tune_pid_blocked_by_sandbox,
    # Server MCP protocol tests
    test_server_initialize_response_spec_compliant,
    test_server_ping_tool_works,
    test_server_tools_list_includes_ping,
    test_server_unknown_tool_returns_error_not_exception,
    test_server_notification_returns_none,
)

TESTS = [
    # ── Sandbox ───────────────────────────────────────────────────────────────
    ("Sandbox: READ_ONLY blocks publish",           test_sandbox_read_only_blocks_publish),
    ("Sandbox: SAFE_WRITE allows allowlisted",      test_sandbox_safe_write_allows_allowlisted),
    ("Sandbox: SAFE_WRITE blocks unknown topic",    test_sandbox_safe_write_blocks_unknown),
    ("Sandbox: FULL allows any topic",              test_sandbox_full_allows_any),
    ("Sandbox: audit log thread-safe (8 threads)",  test_sandbox_audit_log_thread_safe),
    ("Sandbox: dynamic allow_topic()",              test_sandbox_dynamic_allow_topic),
    ("Sandbox: audit summary counts",               test_sandbox_audit_summary),
    ("Sandbox: READ_ONLY blocks set_parameter",     test_sandbox_read_only_blocks_set_parameter),
    # ── Mock Interface ────────────────────────────────────────────────────────
    ("Mock: list_topics has all required topics",   test_mock_list_topics_has_required_topics),
    ("Mock: list_nodes returns (name, ns) tuples",  test_mock_list_nodes_returns_tuples),
    ("Mock: /scan has range_min and 360 rays",      test_mock_read_scan_realistic),
    ("Mock: /battery_state has all fields",         test_mock_read_battery_all_fields),
    ("Mock: /imu/data has orientation quaternion",  test_mock_read_imu_has_orientation),
    ("Mock: ping() returns status=ok",              test_mock_ping),
    ("Mock: latched topic flag preserved",          test_mock_latched_topic),
    ("Mock: publish returns MOCK string",           test_mock_publish_returns_string),
    # ── Diagnostics ───────────────────────────────────────────────────────────
    ("Diagnostics: returns all required fields",    test_diagnostics_returns_valid_structure),
    ("Diagnostics: sensor fault != collision (BUG-03)", test_diagnostics_sensor_fault_not_collision),
    ("Diagnostics: battery pct=None no crash (BUG-04)", test_diagnostics_battery_pct_none_no_crash),
    # ── Topics Tools ──────────────────────────────────────────────────────────
    ("Topics: list_topics() total >= 5",            test_list_topics_total),
    ("Topics: read_topic normalizes slash",         test_read_topic_slash_normalization),
    ("Topics: read_topic passes latched flag",      test_read_topic_latched_flag),
    ("Topics: snapshot fetches in parallel",        test_get_robot_snapshot_parallel),
    # ── Nodes Tools ───────────────────────────────────────────────────────────
    ("Nodes: list_nodes has name+ns+full_name",     test_list_nodes_structure),
    ("Nodes: get_node_info found=True for real node", test_get_node_info_found),
    ("Nodes: get_node_info error for missing node", test_get_node_info_not_found),
    ("Nodes: get_node_info case-sensitive (BUG-11)", test_get_node_info_case_sensitive),
    # ── PID Tools ─────────────────────────────────────────────────────────────
    ("PID: get_pid_state includes bounds",          test_get_pid_state_returns_gains),
    ("PID: negative Kp rejected (BUG-09)",          test_tune_pid_rejects_negative_kp),
    ("PID: extreme Kp value rejected",              test_tune_pid_rejects_extreme_value),
    ("PID: valid gains apply successfully",         test_tune_pid_valid_gains_apply),
    ("PID: no gains provided returns error",        test_tune_pid_no_gains_provided),
    ("PID: blocked by READ_ONLY sandbox",           test_tune_pid_blocked_by_sandbox),
    # ── Server / MCP Protocol ─────────────────────────────────────────────────
    ("Server: initialize response is MCP spec-compliant (BUG-14)", test_server_initialize_response_spec_compliant),
    ("Server: ping tool works (M-01)",              test_server_ping_tool_works),
    ("Server: tools/list includes ping (M-01)",     test_server_tools_list_includes_ping),
    ("Server: unknown tool returns isError=True",   test_server_unknown_tool_returns_error_not_exception),
    ("Server: notification returns None",           test_server_notification_returns_none),
]

passed = 0
failed = 0
errors = []

print()
print("=" * 75)
print(f"  ros2-mcp-server v1.1.0 | Test Suite | {len(TESTS)} tests | Simulation Mode")
print("=" * 75)

for name, fn in TESTS:
    try:
        fn()
        print(f"  [PASS]  {name}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL]  {name}")
        print(f"          {e}")
        errors.append((name, traceback.format_exc()))
        failed += 1

print()
print("-" * 75)
print(f"  Results: {passed} passed, {failed} failed out of {len(TESTS)} tests")

if errors:
    print()
    print("  FAILURE DETAILS:")
    for name, tb in errors:
        print(f"\n  [{name}]")
        for line in tb.strip().splitlines():
            print(f"    {line}")

print("=" * 75)
print()

sys.exit(0 if failed == 0 else 1)
