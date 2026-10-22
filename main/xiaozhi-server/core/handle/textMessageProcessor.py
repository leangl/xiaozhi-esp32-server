import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from core.handle.textMessageHandlerRegistry import TextMessageHandlerRegistry

TAG = __name__


class TextMessageProcessor:
    """Main message processor."""

    def __init__(self, registry: TextMessageHandlerRegistry):
        self.registry = registry

    async def process_message(self, conn: "ConnectionHandler", message: str) -> None:
        """Process an incoming message."""
        try:
            # Parse the JSON message.
            msg_json = json.loads(message)

            # Handle a JSON message.
            if isinstance(msg_json, dict):
                message_type = msg_json.get("type")

                # Log the message.
                conn.logger.bind(tag=TAG).info(f"Received {message_type} message: {message}")

                # Find and invoke the handler.
                handler = self.registry.get_handler(message_type)
                if handler:
                    await handler.handle(conn, msg_json)
                else:
                    conn.logger.bind(tag=TAG).error(f"Received an unknown message type: {message}")
            # Handle a numeric message.
            elif isinstance(msg_json, int):
                conn.logger.bind(tag=TAG).info(f"Received a numeric message: {message}")
                await conn.websocket.send(message)

        except json.JSONDecodeError:
            # Forward non-JSON messages unchanged.
            conn.logger.bind(tag=TAG).error(f"Invalid message while parsing: {message}")
            await conn.websocket.send(message)
