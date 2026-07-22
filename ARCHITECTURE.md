# Architecture & System Design

This document outlines the core architecture of `ros2-mcp-server`, detailing how Model Context Protocol (MCP) clients safely interface with Robot Operating System 2 (ROS2) nodes in a multi-threaded, non-blocking execution environment.

## High-Level Data Flow

```mermaid
graph TD
    Client[AI Client / Claude Desktop] -->|JSON-RPC| Server[ROS2 MCPServer]
    Server -->|Parse & Route| Sandbox[CommandSandbox]
    
    subgraph Execution Layer
    Sandbox -->|Safe O(1) Dispatch| Tools[MCP Tool Handlers]
    Tools -->|Execute| ROS2[ROS2 Interface]
    end
    
    subgraph ROS2 Ecosystem
    ROS2 -->|Subscribe / Read| Topics[(ROS2 Topics)]
    ROS2 -->|Publish / Tune| Nodes[(ROS2 Nodes / PIDs)]
    end
```

## The Dispatch Table & O(1) Routing

Instead of an `if/elif` chain, tool calls are resolved using an O(1) dispatch dictionary located in `server.py`. Each tool schema maps directly to an execution handler defined in `ros2_mcp/tools/`. 
This makes the server endlessly scalable—adding a new tool simply requires defining the handler and registering the schema.

## Multi-Threaded Executor Model

ROS2 operates asynchronously, whereas MCP tool executions are synchronous requests from the AI client.
To bridge this:
1. **Daemon Spin Thread**: `rclpy.spin()` runs in a dedicated daemon thread via a `MultiThreadedExecutor`.
2. **Synchronous Bridging**: MCP tool requests trigger `_wait_for_future` or immediate polling mechanisms that read from latched caches or block *only* the tool execution thread, preventing the ROS2 spin thread from deadlocking.

## Safety & The Sandbox (`CommandSandbox`)

The AI's operational permissions are governed by the `CommandSandbox`. This prevents autonomous agents from taking destructive actions (e.g., publishing `cmd_vel` directly into a wall).

See [SECURITY.md](SECURITY.md) for a deep dive into the threat model and permission levels.
