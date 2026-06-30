from __future__ import annotations

import sys
import types
from pathlib import Path


if "blinker" not in sys.modules:
    blinker = types.ModuleType("blinker")

    class Signal:
        def __init__(self, *args, **kwargs) -> None:
            self._receivers = []

        def connect(self, receiver, sender=None, weak=True):  # noqa: ARG002
            self._receivers.append((receiver, sender))
            return receiver

        def disconnect(self, receiver=None, sender=None):  # noqa: ARG002
            if receiver is None and sender is None:
                self._receivers.clear()
                return True
            before = len(self._receivers)
            self._receivers = [item for item in self._receivers if item != (receiver, sender)]
            return len(self._receivers) != before

        def send(self, *args, **kwargs):
            event_sender = args[0] if args else None
            payload_args = args[1:] if args else ()
            results = []
            for receiver, _sender in list(self._receivers):
                if receiver is not None:
                    results.append((receiver, receiver(event_sender, *payload_args, **kwargs)))
            return results

    class Namespace:
        def signal(self, *args, **kwargs):
            return Signal(*args, **kwargs)

    blinker.Signal = Signal
    blinker.ANY = object()
    blinker.Namespace = Namespace
    sys.modules["blinker"] = blinker

import streamlit as st


STARTER_ROOT = Path(__file__).resolve().parents[1]
if str(STARTER_ROOT) not in sys.path:
    sys.path.insert(0, str(STARTER_ROOT))

from research_summarizer_ai_agent.agents import build_view_model  # noqa: E402
from research_summarizer_ai_agent.agents import get_openrouter_model_name  # noqa: E402
from research_summarizer_ai_agent.agents import get_runtime_mode  # noqa: E402
from research_summarizer_ai_agent.agents import run_simple_agent  # noqa: E402


st.set_page_config(page_title="Simple Research Agent", page_icon="R", layout="wide")
st.title("Simple Research Agent")
st.caption("Send a prompt to one LangChain agent that can search the web and read pages.")

with st.sidebar:
    st.subheader("Runtime")
    runtime_mode = get_runtime_mode()
    st.caption(f"Mode: {runtime_mode}")
    if runtime_mode == "openrouter":
        st.caption(f"Model: {get_openrouter_model_name()}")

user_input = st.text_area(
    "Your input",
    placeholder="Ask the agent something like: Summarize the latest ideas behind AI research agents.",
    height=140,
)

if st.button("Run Agent", type="primary"):
    if not user_input.strip():
        st.warning("Enter a prompt first.")
    else:
        result = run_simple_agent(user_input)
        view_model = build_view_model(result)

        if bool(view_model["used_fallback"]):
            st.warning("Fallback response was used.")
            if str(view_model["error_message"]).strip():
                st.code(str(view_model["error_message"]))

        st.subheader("Response")
        st.markdown(str(view_model["response"]))

        if view_model["sources"]:
            st.markdown("### Sources")
            for url in view_model["sources"]:
                st.write(f"- {url}")
