# Launch Orchestration Strategy

To achieve the "Velocity Spike" and hit 2,000+ stars, execution timing and presentation are everything. Follow this orchestration checklist exactly.

## 1. The Visual Hook (Pre-Launch Prep)
- [ ] You must record the 15-second visual hook. Open Claude Desktop on one half of your screen and a Gazebo simulation (or camera feed of your physical robot) on the other.
- [ ] Type: `"Tune the PID to stop the oscillation"` into Claude.
- [ ] Record the robot immediately stabilizing as Claude calls the `tune_pid` MCP tool.
- [ ] Save this as `docs/assets/demo.gif` or a high-quality `.mp4`.

## 2. Timing
**Target Launch Window:** Tuesday or Wednesday at **7:00 AM EST (US Time)**.
This hits the morning coffee scroll for the East Coast, the afternoon for Europe, and allows momentum to build before the West Coast wakes up.

## 3. The X (Twitter) Drop
Post a thread to maximize reach.

**Tweet 1 (The Hook & Video):**
> I just connected Claude directly to my physical robot using the new Model Context Protocol (MCP).
> 
> No more copy-pasting ROS2 sensor dumps. I just ask Claude to "tune the PID" or "check the LiDAR," and it executes it on the hardware instantly.
> 
> Open Sourced it today. 🤯👇
> [Attach your 15-second video]

**Tweet 2 (The Details & Tags):**
> `ros2-mcp-server` creates a live, bidirectional bridge between any MCP-compatible AI agent and a ROS2 system.
> 
> It features an execution sandbox (safe_write) so the AI can't accidentally crash the robot.
> 
> GitHub: https://github.com/EngineerAbdullahBinZafar/ros2-mcp-server
> 
> @AnthropicAI @alexalbert__ #ROS2 #MCP #Robotics

## 4. Hacker News Submission
- **Title:** `Show HN: The world's first Model Context Protocol (MCP) server for ROS2`
- **Link:** Direct to your GitHub repository.
- **First Comment:** Write a short welcome comment explaining *why* you built it. 
  *Example:* "Hey HN, I'm a Mechatronics student who got tired of copying 10,000 lines of ROS2 terminal output into Claude just to debug my drone. I built this MCP server so Claude can read the `/scan` and `/imu/data` topics directly, and even adjust parameters on the fly in a sandboxed environment. Happy to answer questions!"

## 5. Post-Launch
- Monitor the GitHub Issues tab. The new Issue Templates will handle the bug reports cleanly.
- If you see traffic surging, pin the repository to your GitHub profile.
