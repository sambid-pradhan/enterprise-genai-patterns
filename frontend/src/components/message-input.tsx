"use client";

type MessageInputProps = {
  value: string;
  disabled?: boolean;
  placeholder?: string;
  onChange: (value: string) => void;
  onSend: () => void;
};

export function MessageInput({
  value,
  disabled = false,
  placeholder = "Ask for a recipe, a clarification, or a structured recommendation...",
  onChange,
  onSend
}: MessageInputProps) {
  return (
    <form
      className="input-bar"
      onSubmit={(event) => {
        event.preventDefault();
        onSend();
      }}
    >
      <label className="sr-only" htmlFor="chat-message">
        Message
      </label>
      <textarea
        id="chat-message"
        className="input-bar__textarea"
        rows={1}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onSend();
          }
        }}
      />
      <button className="input-bar__button" type="submit" disabled={disabled || !value.trim()}>
        {disabled ? "Sending..." : "Send"}
      </button>
    </form>
  );
}

