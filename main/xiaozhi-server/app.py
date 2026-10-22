import sys
import uuid
import signal
import asyncio
from aioconsole import ainput
from config.settings import load_config
from config.logger import setup_logging
from core.utils.util import get_local_ip, validate_mcp_endpoint
from config.service_policy import validate_endpoint, ServicePolicyError
from core.http_server import SimpleHttpServer
from core.websocket_server import WebSocketServer
from core.utils.util import check_ffmpeg_installed
from core.utils.gc_manager import get_gc_manager

TAG = __name__
logger = setup_logging()


async def wait_for_exit() -> None:
    """
    Wait until Ctrl‑C / SIGTERM is received.
    - Unix: use add_signal_handler.
    - Windows: rely on KeyboardInterrupt.
    """
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    if sys.platform != "win32":  # Unix / macOS
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await stop_event.wait()
    else:
        # On Windows, await a future that never completes. Let KeyboardInterrupt
        # reach asyncio.run so leftover non-daemon threads do not block process exit.
        try:
            await asyncio.Future()
        except KeyboardInterrupt:  # Ctrl‑C
            pass


async def monitor_stdin():
    """Monitor standard input and consume Enter key presses."""
    while True:
        await ainput()  # Wait asynchronously for input and consume Enter.


async def main():
    check_ffmpeg_installed()
    config = await load_config()

    # auth_key precedence: server.auth_key > manager-api.secret > generated value.
    # Used for JWT authentication (vision), OTA tokens and WebSocket authentication.
    # Read auth_key from configuration.
    auth_key = config["server"].get("auth_key", "")
    
    # Validate auth_key; fall back to manager-api.secret if invalid.
    if not auth_key or len(auth_key) == 0 or "你" in auth_key:
        auth_key = config.get("manager-api", {}).get("secret", "")
        # Validate the secret; generate a random key if invalid.
        if not auth_key or len(auth_key) == 0 or "你" in auth_key:
            auth_key = str(uuid.uuid4().hex)
    
    config["server"]["auth_key"] = auth_key

    # Add the standard-input monitoring task.
    stdin_task = asyncio.create_task(monitor_stdin())

    # Start the global GC manager (clean up every five minutes).
    gc_manager = get_gc_manager(interval_seconds=300)
    await gc_manager.start()

    # Start the WebSocket server.
    ws_server = WebSocketServer(config)
    ws_task = asyncio.create_task(ws_server.start())
    # Start the simple HTTP server.
    ota_server = SimpleHttpServer(config)
    ota_task = asyncio.create_task(ota_server.start())

    read_config_from_api = config.get("read_config_from_api", False)
    port = int(config["server"].get("http_port", 8003))
    if not read_config_from_api:
        logger.bind(tag=TAG).info(
            "OTA endpoint:\t\thttp://{}:{}/xiaozhi/ota/",
            get_local_ip(),
            port,
        )
    logger.bind(tag=TAG).info(
        "Vision endpoint:\thttp://{}:{}/mcp/vision/explain",
        get_local_ip(),
        port,
    )
    mcp_endpoint = config.get("mcp_endpoint", None)
    if mcp_endpoint is not None and "你" not in mcp_endpoint:
        # Validate the MCP endpoint format.
        try:
            validate_endpoint(mcp_endpoint, "mcp")
            if not validate_mcp_endpoint(mcp_endpoint):
                raise ServicePolicyError("Invalid MCP endpoint format")
            logger.bind(tag=TAG).info("Reviewed MCP endpoint configured")
            # Convert the MCP connection endpoint to a call endpoint.
            mcp_endpoint = mcp_endpoint.replace("/mcp/", "/call/")
            config["mcp_endpoint"] = mcp_endpoint
        except ServicePolicyError:
            logger.bind(tag=TAG).error("MCP endpoint unavailable; configure a reviewed endpoint")
            config["mcp_endpoint"] = ""

    # Read WebSocket configuration with safe defaults.
    websocket_port = 8000
    server_config = config.get("server", {})
    if isinstance(server_config, dict):
        websocket_port = int(server_config.get("port", 8000))

    logger.bind(tag=TAG).info(
        "WebSocket URL:\tws://{}:{}/xiaozhi/v1/",
        get_local_ip(),
        websocket_port,
    )

    logger.bind(tag=TAG).info(
        "=======The URL above uses WebSocket; do not open it directly in a browser======="
    )
    logger.bind(tag=TAG).info(
        "To test WebSocket, start the digital-human module and use its browser interface"
    )
    logger.bind(tag=TAG).info(
        "=============================================================\n"
    )

    try:
        await wait_for_exit()  # Wait for a shutdown signal.
    except asyncio.CancelledError:
        print("Task cancelled; cleaning up resources...")
    finally:
        # Stop the global GC manager.
        await gc_manager.stop()

        # Cancel all tasks (essential to the shutdown fix).
        stdin_task.cancel()
        ws_task.cancel()
        if ota_task:
            ota_task.cancel()

        # Wait for tasks to stop, with a required timeout.
        await asyncio.wait(
            [stdin_task, ws_task, ota_task] if ota_task else [stdin_task, ws_task],
            timeout=3.0,
            return_when=asyncio.ALL_COMPLETED,
        )
        print("Server shut down; exiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user; exiting.")
