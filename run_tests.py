"""
ros2-mcp-server Test Runner
Runs all 13 unit tests in simulation mode (no ROS2 required).
"""
import sys
import os
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from test.test_server import (
    test_sandbox_read_only_blocks_publish,
    test_sandbox_safe_write_allows_allowlisted_topic,
    test_sandbox_safe_write_blocks_unknown_topic,
    test_sandbox_full_mode_allows_any_topic,
    test_sandbox_audit_log,
    test_sandbox_allow_topic_dynamic,
    test_mock_interface_list_topics,
    test_mock_interface_read_scan,
    test_mock_interface_read_battery,
    test_mock_interface_publish,
    test_diagnostics_returns_status,
    test_list_topics,
    test_read_topic_normalizes_slash,
)

TESTS = [
    ("Sandbox: READ_ONLY blocks publish",      test_sandbox_read_only_blocks_publish),
    ("Sandbox: SAFE_WRITE allows allowlist",   test_sandbox_safe_write_allows_allowlisted_topic),
    ("Sandbox: SAFE_WRITE blocks unknown",     test_sandbox_safe_write_blocks_unknown_topic),
    ("Sandbox: FULL allows any topic",         test_sandbox_full_mode_allows_any_topic),
    ("Sandbox: audit log records decisions",   test_sandbox_audit_log),
    ("Sandbox: dynamic allow_topic()",         test_sandbox_allow_topic_dynamic),
    ("MockInterface: list_topics()",           test_mock_interface_list_topics),
    ("MockInterface: /scan has 360 ranges",   test_mock_interface_read_scan),
    ("MockInterface: /battery voltage range", test_mock_interface_read_battery),
    ("MockInterface: publish returns string", test_mock_interface_publish),
    ("Diagnostics: returns system_status",    test_diagnostics_returns_status),
    ("Tools: list_topics() total >= 5",        test_list_topics),
    ("Tools: read_topic() normalizes slash",  test_read_topic_normalizes_slash),
]

passed = 0
failed = 0

print()
print("=" * 70)
print("  ros2-mcp-server | Test Suite (Simulation Mode)")
print("=" * 70)

for name, fn in TESTS:
    try:
        fn()
        print(f"  [PASS]  {name}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL]  {name}")
        print(f"          {e}")
        failed += 1

print()
print("-" * 70)
print(f"  Results: {passed} passed, {failed} failed out of {len(TESTS)} tests")
print("=" * 70)
print()

sys.exit(0 if failed == 0 else 1)
