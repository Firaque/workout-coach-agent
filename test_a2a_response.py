import asyncio
import os
import uuid
import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Part,
    Role,
    TextPart,
    DataPart,
    FilePart,
    TaskArtifactUpdateEvent,
    TransportProtocol,
)

RESOURCE = "projects/967591342130/locations/us-east1/reasoningEngines/392224384930021376"
AGENT_DIRECTORY = "app"
LOCATION = "us-east1"

A2A_BASE = f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"

_creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

def _auth_headers():
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }

_A2UI_MIME = "application/json+a2ui"

def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        root = getattr(p, "root", p)
        if isinstance(root, TextPart) and getattr(root, "text", None):
            out.append({"kind": "text", "text": root.text})
        elif getattr(root, "data", None) is not None:
            meta = getattr(root, "metadata", None) or {}
            mime = meta.get("mimeType") if isinstance(meta, dict) else None
            if mime == _A2UI_MIME:
                out.append({"kind": "a2ui", "data": root.data})
        elif isinstance(root, FilePart):
            uri = getattr(getattr(root, "file", None), "uri", None)
            if uri:
                out.append({"kind": "text", "text": uri})
    return out

async def main():
    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        resp = await client.get(A2A_CARD_URL)
        card = AgentCard(**resp.json())
        card.url = A2A_BASE

        factory = ClientFactory(
            ClientConfig(
                supported_transports=[
                    TransportProtocol.jsonrpc,
                    TransportProtocol.http_json,
                ],
                httpx_client=client,
            )
        )
        a2a_client = factory.create(card)

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.user,
            parts=[Part(root=TextPart(text="What chest exercises should I do?"))],
        )

        parts = []
        last_task = None
        async for event in a2a_client.send_message(msg):
            if not isinstance(event, tuple):
                continue
            task, update = event
            if task is not None:
                last_task = task
            if isinstance(update, TaskArtifactUpdateEvent):
                parts.extend(_extract_parts(update.artifact.parts))

        if not parts and last_task is not None:
            # Check last_task history for agent messages
            for history_msg in getattr(last_task, "history", []) or []:
                role = getattr(history_msg, "role", None)
                if role == Role.agent or role == "agent":
                    parts.extend(_extract_parts(getattr(history_msg, "parts", [])))

        print("Extracted parts count:", len(parts))
        print("Parts sample:", parts[:2])

asyncio.run(main())
