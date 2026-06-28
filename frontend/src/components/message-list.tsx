"use client";

import { useEffect, useRef } from "react";
import { StructuredRenderer } from "@/components/structured-renderer";
import type { ChatMessage } from "@/lib/chat-types";

type MessageListProps = {
  messages: ChatMessage[];
  onSuggestionSelect?: (value: string) => void;
};

export function MessageList({ messages, onSuggestionSelect }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (!messages.length) {
    return (
      <div className="empty-state">
        <p className="structured-kicker">MVP chat UI</p>
        <h2>Start with an ingredient, a goal, or a vague request.</h2>
        <p>
          The assistant will return plain chat text plus structured UI blocks for recipes, follow-up questions, and
          lists.
        </p>
      </div>
    );
  }

  return (
    <div className="message-list" aria-live="polite">
      {messages.map((message) => (
        <article
          className={`message-row message-row--${message.role}`}
          key={message.id}
          aria-label={`${message.role} message`}
        >
          <div className={`message-bubble message-bubble--${message.role}`}>
            <div className="message-bubble__header">
              <span className="message-bubble__role">{message.role}</span>
              {message.isPending ? <span className="message-bubble__status">thinking</span> : null}
              {message.isError ? <span className="message-bubble__status message-bubble__status--error">error</span> : null}
            </div>
            {message.content ? <p className="message-text">{message.content}</p> : null}
            {message.structuredBlocks?.length ? (
              <StructuredRenderer blocks={message.structuredBlocks} onAction={onSuggestionSelect} />
            ) : null}
          </div>
        </article>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

