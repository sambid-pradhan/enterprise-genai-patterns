"use client";

import { useState } from "react";
import { MessageInput } from "@/components/message-input";
import { MessageList } from "@/components/message-list";
import { sendChatMessage } from "@/lib/chat-client";
import type { ChatMessage } from "@/lib/chat-types";

const DEFAULT_PROMPTS = [
  "Suggest a quick dinner with chicken, rice, and spinach.",
  "Ask me one clarifying question before you answer.",
  "Give me a concise recipe card with ingredients and steps."
];

function createId() {
  return crypto.randomUUID();
}

export function ChatShell() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sessionId] = useState(() => createId());

  async function submitMessage(text: string) {
    const content = text.trim();
    if (!content || isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content
    };
    const pendingId = createId();
    const pendingMessage: ChatMessage = {
      id: pendingId,
      role: "assistant",
      content: "Thinking...",
      isPending: true
    };

    const history = [...messages, userMessage].map(({ role, content }) => ({ role, content }));

    setMessages((current) => [...current, userMessage, pendingMessage]);
    setDraft("");
    setIsSending(true);

    try {
      const response = await sendChatMessage({
        sessionId,
        message: content,
        history
      });

      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content: response.assistantMessage,
        structuredBlocks: response.structuredBlocks
      };

      setMessages((current) => current.map((message) => (message.id === pendingId ? assistantMessage : message)));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Something went wrong while contacting chat.";

      setMessages((current) =>
        current.map((message) =>
          message.id === pendingId
            ? {
                ...message,
                content: errorMessage,
                isPending: false,
                isError: true
              }
            : message
        )
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="chat-shell">
      <header className="chat-shell__header">
        <div>
          <p className="hero-kicker">Frontend MVP</p>
          <h1 className="hero-title">Structured chat for grounded recipe guidance.</h1>
        </div>
        <p className="hero-copy">
          This shell sends turns to the backend chat endpoint and renders both plain text and structured UI blocks.
        </p>
      </header>

      <div className="chat-shell__surface">
        <MessageList messages={messages} onSuggestionSelect={submitMessage} />

        {!messages.length ? (
          <div className="empty-actions" aria-label="Suggested prompts">
            {DEFAULT_PROMPTS.map((prompt) => (
              <button
                className="empty-actions__button"
                key={prompt}
                type="button"
                onClick={() => submitMessage(prompt)}
                disabled={isSending}
              >
                {prompt}
              </button>
            ))}
          </div>
        ) : null}

        <MessageInput
          value={draft}
          disabled={isSending}
          onChange={setDraft}
          onSend={() => submitMessage(draft)}
        />
      </div>
    </section>
  );
}

