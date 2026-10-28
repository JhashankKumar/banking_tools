import { Send } from "lucide-react";
import { useState } from "react";

export function AskBox({
  placeholder,
  disabled,
  onAsk,
}: {
  placeholder: string;
  disabled: boolean;
  onAsk: (question: string) => void;
}) {
  const [text, setText] = useState("");
  const submit = () => {
    const question = text.trim();
    if (!question || disabled) return;
    onAsk(question);
    setText("");
  };
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      className="flex items-center gap-2 rounded-xl border border-line bg-surface py-1.5 pr-1.5 pl-3"
    >
      <label className="sr-only" htmlFor="copilot-question">
        Ask the copilot
      </label>
      <input
        id="copilot-question"
        value={text}
        maxLength={1000}
        disabled={disabled}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-transparent text-xs text-ink outline-none placeholder:text-muted disabled:opacity-60"
      />
      <button
        type="submit"
        aria-label="Send"
        disabled={disabled || !text.trim()}
        className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-on-primary disabled:opacity-50"
      >
        <Send aria-hidden size={14} />
      </button>
    </form>
  );
}
