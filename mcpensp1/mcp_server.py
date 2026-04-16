import asyncio
import json
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

MCP_SERVER_NAME = "ensp-mcp-server"
SERVER_URL = "http://127.0.0.1:5000"

mcp_server = Server(MCP_SERVER_NAME)


async def mcp_call_tool(name: str, arguments: dict):
    async with httpx.AsyncClient(timeout=30.0) as client:
        if name == "scan_devices":
            params = {
                "start": arguments.get("start", 2000),
                "end": arguments.get("end", 2050)
            }
            resp = await client.get(f"{SERVER_URL}/api/devices/scan", params=params)
            return [TextContent(type="text", text=resp.text)]

        elif name == "connect_device":
            resp = await client.post(f"{SERVER_URL}/api/devices/connect", json={"port": arguments["port"]})
            return [TextContent(type="text", text=resp.text)]

        elif name == "send_command":
            resp = await client.post(f"{SERVER_URL}/api/devices/command", json={
                "path": arguments["path"],
                "command": arguments["command"]
            })
            return [TextContent(type="text", text=resp.text)]

        elif name == "disconnect_device":
            resp = await client.post(f"{SERVER_URL}/api/devices/disconnect", json={"path": arguments["path"]})
            return [TextContent(type="text", text=resp.text)]

        elif name == "get_connected_devices":
            resp = await client.get(f"{SERVER_URL}/api/devices")
            return [TextContent(type="text", text=resp.text)]

        elif name == "rename_device":
            resp = await client.post(f"{SERVER_URL}/api/devices/rename", json={
                "path": arguments["path"],
                "name": arguments["name"]
            })
            return [TextContent(type="text", text=resp.text)]

        elif name == "get_topology":
            resp = await client.get(f"{SERVER_URL}/api/topology")
            return [TextContent(type="text", text=resp.text)]

        elif name == "save_topology":
            resp = await client.post(f"{SERVER_URL}/api/topology", json=arguments.get("data", {}))
            return [TextContent(type="text", text=resp.text)]

        else:
            return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))]


@mcp_server.list_tools()
async def list_tools():
    return [
        Tool(
            name="scan_devices",
            description="Scan for eNSP devices on specified port range",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {"type": "integer", "description": "Start port (default 2000)", "default": 2000},
                    "end": {"type": "integer", "description": "End port (default 2050)", "default": 2050}
                }
            }
        ),
        Tool(
            name="connect_device",
            description="Connect to an eNSP device by port",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Device port number"}
                },
                "required": ["port"]
            }
        ),
        Tool(
            name="send_command",
            description="Send a command to a connected eNSP device",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Device path (e.g. 127.0.0.1:2000)"},
                    "command": {"type": "string", "description": "Command to send"}
                },
                "required": ["path", "command"]
            }
        ),
        Tool(
            name="disconnect_device",
            description="Disconnect from an eNSP device",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Device path (e.g. 127.0.0.1:2000)"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="get_connected_devices",
            description="Get list of all connected eNSP devices",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="rename_device",
            description="Rename an eNSP device for easier identification",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Device path"},
                    "name": {"type": "string", "description": "New device name"}
                },
                "required": ["path", "name"]
            }
        ),
        Tool(
            name="get_topology",
            description="Get the current topology data (uploaded from Web UI)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="save_topology",
            description="Save or update topology data via MCP",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Topology data object to save"}
                }
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        return await mcp_call_tool(name, arguments)
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def run_mcp_server():
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())


if __name__ == '__main__':
    print("eNSP MCP Server starting...")
    print(f"Connecting to main server at {SERVER_URL}")
    print("Make sure the main server (app.py) is running first!")
    asyncio.run(run_mcp_server())
