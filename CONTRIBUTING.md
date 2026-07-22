# Contributing to ros2-mcp-server

Thank you for considering a contribution. This project follows simple, clear guidelines to keep the codebase production-quality for real robotics deployments.

---

## Quick Start

```bash
git clone https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server
cd ros2-mcp-server
pip install -e ".[dev]"

# Run the test suite (no ROS2 required)
python run_tests.py
```

---

## What We Welcome

| Type | Examples |
|:---|:---|
| Bug fixes | Correct a tool's output, fix an edge case |
| New MCP tools | `navigate_to_pose`, `record_rosbag`, `list_services` |
| New transport | rosbridge WebSocket, ROS2 DDS daemon |
| Better mock data | More realistic simulation sensor values |
| Documentation | Deployment guides, robot-specific examples |
| CI / packaging | New OS targets, Docker images |

---

## Code Standards

1. **All PRs must pass the test suite.** `python run_tests.py` must show 0 failures.
2. **No phantom dependencies.** Only add to `pyproject.toml` if the package is actually imported.
3. **New tools need a JSON Schema.** Add your tool's `inputSchema` to `TOOL_SCHEMAS` in `server.py`.
4. **Sandbox first.** Any tool that writes to hardware must go through `CommandSandbox.check_publish()` or `check_set_parameter()`.
5. **Tests for every new tool.** At minimum: one happy-path test + one error-path test.
6. **Type hints required.** All public functions must have complete type annotations.

---

## Adding a New MCP Tool

1. Create your handler in `ros2_mcp/tools/your_tool.py`
2. Export it from `ros2_mcp/tools/__init__.py`
3. Add the JSON Schema to `TOOL_SCHEMAS` in `server.py`
4. Add the handler to `_build_dispatch()` in `server.py`
5. Write tests in `test/test_server.py`
6. Update the tool table in `README.md`

---

## Safety Rules (Non-Negotiable)

- **Never bypass the sandbox.** Every hardware write goes through `CommandSandbox`.
- **Never set `SAFETY_LEVEL=full` as a default.** It must be explicitly opted in.
- **Bounds-check all numeric parameters.** See `tools/pid.py` for the pattern.
- **Validate before hardware.** All validation must happen before any ROS2 call.

---

## Pull Request Process

1. Fork the repo and create a branch: `git checkout -b fix/your-bug-description`
2. Make your changes with tests
3. Run `python run_tests.py` — all must pass
4. Open a PR with a clear description of what you changed and why
5. The CI will run automatically (GitHub Actions)

---

## Reporting Bugs

Open an [issue](https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server/issues) with:
- Your ROS2 distro (Humble / Iron / Jazzy)
- Your robot platform (Jetson Orin, RPi 4, simulation)
- The `SAFETY_LEVEL` you were using
- The exact error message or unexpected behavior

---

## Code of Conduct

Be professional. This project is used on physical robots. Unclear, untested, or unsafe code review comments are not welcome.
