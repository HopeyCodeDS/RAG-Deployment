import type { Message } from "../App";
import SourceList from "./SourceList";
import styles from "../styles/ChatMessage.module.css";

interface Props {
  message: Message;
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      className={`${styles.row} ${isUser ? styles.userRow : styles.assistantRow}`}
    >
      <div
        className={`${styles.bubble} ${isUser ? styles.userBubble : styles.assistantBubble}`}
      >
        <p className={styles.text}>{message.text}</p>
        {message.sources && message.sources.length > 0 && (
          <SourceList sources={message.sources} />
        )}
      </div>
    </div>
  );
}
