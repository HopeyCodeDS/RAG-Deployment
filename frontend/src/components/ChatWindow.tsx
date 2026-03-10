import React, { type RefObject } from "react";
import type { Message } from "../App";
import ChatMessage from "./ChatMessage";
import LoadingBubble from "./LoadingBubble";
import styles from "../styles/ChatWindow.module.css";

interface Props {
  messages: Message[];
  isLoading: boolean;
  bottomRef: RefObject<HTMLDivElement | null>;
  onPromptClick?: (text: string) => void;
}

const SAMPLE_PROMPTS = [
  "What services do you offer?",
  "Tell me about pricing",
  "How do I get started?",
];

export default function ChatWindow({
  messages,
  isLoading,
  bottomRef,
  onPromptClick,
}: Props) {
  return (
    <div
      className={styles.window}
      role="log"
      aria-live="polite"
      aria-label="Conversation"
    >
      {messages.length === 0 && !isLoading && (
        <div className={styles.empty}>
          <svg
            className={styles.emptyBolt}
            viewBox="0 0 64 64"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M38 8 L14 36 L28 36 L24 56 L50 28 L36 28 Z"
              fill="#00f0ff"
            />
          </svg>
          <p className={styles.emptyTitle}>What can I help you find?</p>
          <p className={styles.emptyHint}>
            Ask anything about the knowledge base. I'll find the most relevant
            information and cite my sources.
          </p>
          {onPromptClick && (
            <div className={styles.emptyPrompts}>
              {SAMPLE_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  className={styles.promptChip}
                  onClick={() => onPromptClick(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      {isLoading && <LoadingBubble />}
      <div
        ref={bottomRef as React.RefObject<HTMLDivElement>}
        aria-hidden="true"
      />
    </div>
  );
}
