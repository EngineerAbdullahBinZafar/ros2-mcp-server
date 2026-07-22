"""MCP Tools for ROS2 Node Introspection."""
from typing import Any, Dict, List


def handle_list_nodes(ros2: Any) -> Dict:
    nodes = ros2.list_nodes()
    return {"total": len(nodes), "nodes": sorted(nodes)}


def handle_get_node_info(ros2: Any, node_name: str) -> Dict:
    all_topics = ros2.list_topics()
    related = [t for t in all_topics if node_name.lower() in str(t).lower()]
    return {
        "node": node_name,
        "related_topics": related,
        "note": "For full pub/sub graph, use rqt_graph or 'ros2 node info' in a live environment."
    }
