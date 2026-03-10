import { useState, type KeyboardEvent, type FormEvent } from "react";
import styles from "../styles/QueryInput.module.css";

interface Props {
  onSubmit: (text: string) => void;
  isLoading: boolean;
}

const MAX_LENGTH = 1000;

export default function QueryInput({ onSubmit, isLoading }: Props) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed);
    setValue("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const trimmed = value.trim();
      if (!trimmed || isLoading) return;
      onSubmit(trimmed);
      setValue("");
    }
  }

  const remaining = MAX_LENGTH - value.length;
  const isOverLimit = remaining < 0;

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <div className={styles.inputWrapper}>
        <textarea
          className={styles.textarea}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question..."
          rows={1}
          disabled={isLoading}
          aria-label="Query input"
          aria-describedby="char-count"
        />
        <button
          type="submit"
          className={styles.sendButton}
          disabled={isLoading || !value.trim() || isOverLimit}
          aria-label="Send query"
        >
          {isLoading ? (
            <span className={styles.spinner} aria-hidden="true" />
          ) : (
            "Send"
          )}
        </button>
      </div>
      <span
        id="char-count"
        className={`${styles.charCount} ${isOverLimit ? styles.overLimit : ""}`}
      >
        {remaining} characters remaining
      </span>
    </form>
  );
}
