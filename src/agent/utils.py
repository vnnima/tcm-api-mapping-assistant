import re
from typing import Dict, Optional, Sequence, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


URL_RE = re.compile(r"https?://[^\s]+", re.I)


def parse_endpoints(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not text:
        return out
    urls = URL_RE.findall(text)
    # assume order of URLs is test then prod
    if len(urls) == 2:
        out["test_endpoint"] = urls[0]
        out["prod_endpoint"] = urls[1]
        return out
    # Otherwise, try keyword-based classification
    for line in text.splitlines():
        low = line.lower()
        m = URL_RE.search(line)
        if not m:
            continue
        if "test" in low:
            out["test_endpoint"] = m.group(0)
        if "prod" in low or "production" in low:
            out["prod_endpoint"] = m.group(0)
    return out


def parse_client_ident(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"clientIdentCode\s*[:=]\s*([A-Za-z0-9_\-]+)", text, re.I)
    if m:
        return m.group(1)
    m = re.search(r"mandant(?:enname)?\s*[:=]\s*([A-Za-z0-9_\-]+)", text, re.I)
    if m:
        return m.group(1)
    tokens = re.findall(r"\b[A-Z0-9_]{3,12}\b", text)
    return tokens[0] if tokens else None


def parse_wsm_user(text: str) -> Optional[bool]:
    if not text:
        return None
    low = text.strip().lower()
    if any(w in low for w in ["yes", "ja", "y", "configured", "done", "gesetzt", "vorhanden"]):
        return True
    if any(w in low for w in ["no", "nein", "n", "not yet", "nicht", "fehlt"]):
        return False
    return None


def parse_yes_no(text: str) -> Optional[bool]:
    if not text:
        return None
    low = text.strip().lower()

    # Direct matches first
    if low in {"yes", "y", "ja", "j", "1", "true", "ok"}:
        return True
    if low in {"no", "n", "nein", "0", "false"}:
        return False

    # Substring matches for longer responses
    if any(word in low for word in ["ja", "yes", "okay", "klar"]):
        return True
    if any(word in low for word in ["nein", "no", "nicht"]):
        return False

    return None


def has_endpoint_information(prov: Dict[str, str]) -> bool:
    return any(prov.get(key) for key in ["test_endpoint", "prod_endpoint"])


def format_endpoints_message(found: Dict[str, str]) -> List[str]:
    lines = []
    if found.get("test_endpoint"):
        lines.append(f"- Test: {found['test_endpoint']}")
    if found.get("prod_endpoint"):
        lines.append(f"- Prod:  {found['prod_endpoint']}")
    if len(lines) == 1:
        lines.append(
            "Hinweis: Den zweiten Endpoint (Test/Prod) können Sie später ergänzen.")
    return lines


def get_last_user_message(messages: Sequence[BaseMessage]) -> str:
    """Extract the content from the last human message."""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                return " ".join(
                    part["text"] for part in content if isinstance(part, dict) and "text" in part
                )
    return ""


def get_latest_user_message(messages: Sequence[BaseMessage]) -> str:
    """Extract the content from the last message, regardless of type."""
    if not messages:
        return ""
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        content = last_message.content
        if isinstance(content, str):
            return content
        # TODO: Why does the content from the chat look different?
        elif isinstance(content, list):
            return " ".join(
                part["text"] for part in content if isinstance(part, dict) and "text" in part
            )
    return ""


def get_last_assistant_message(messages: Sequence[BaseMessage]) -> str:
    """Extract the content from the last assistant message."""
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                return " ".join(
                    part["text"] for part in content if isinstance(part, dict) and "text" in part
                )
    return ""


def get_message_content(message: BaseMessage) -> str:
    """Extract string content from any message."""
    content = message.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return " ".join(
            part["text"] for part in content if isinstance(part, dict) and "text" in part
        )
    return ""