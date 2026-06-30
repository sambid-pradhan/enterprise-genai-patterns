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
            self._receivers = [
                item for item in self._receivers if item != (receiver, sender)
            ]
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

from research_summarizer_ai_agent.pipeline import run_research  # noqa: E402
from research_summarizer_ai_agent.planner import build_research_plan  # noqa: E402
from research_summarizer_ai_agent.synthesizer import build_report_markdown  # noqa: E402


st.set_page_config(page_title="Research Summarizer", page_icon="R", layout="wide")
st.title("Research Summarizer")
st.caption("Search multiple primary sources and synthesize a sectioned digest.")

topic = st.text_input("Topic or question", placeholder="e.g. How do research summarizers work?")

if st.button("Research", type="primary"):
    if not topic.strip():
        st.warning("Enter a topic or question first.")
    else:
        try:
            plan = build_research_plan(topic)
            report = run_research(topic)
        except Exception as exc:
            st.error(f"Research failed: {exc}")
        else:
            st.subheader("Planned sub-questions")
            for question in plan.sub_questions:
                st.write(f"- {question}")

            st.subheader("Report")
            st.markdown(build_report_markdown(plan, report))
