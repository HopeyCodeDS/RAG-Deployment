import React, { type RefObject } from "react";
import type { Message } from "../App";
import ChatMessage from "./ChatMessage";
import LoadingBubble from "./LoadingBubble";
import styles from "../styles/ChatWindow.module.css";

interface Props {
  messages: Message[];
  isLoading: boolean;
  bottomRef: RefObject<HTMLDivElement | null>;
}

export default function ChatWindow({ messages, isLoading, bottomRef }: Props) {
  return (
    <div
      className={styles.window}
      role="log"
      aria-live="polite"
      aria-label="Conversation"
    >
      {messages.length === 0 && !isLoading && (
        <p className={styles.empty}>Ask anything about the knowledge base.</p>
      )}
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      {isLoading && <LoadingBubble />}
      <div ref={bottomRef as React.RefObject<HTMLDivElement>} aria-hidden="true" />
    </div>
  );
}
