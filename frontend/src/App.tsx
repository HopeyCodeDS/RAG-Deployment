import { useState, useRef, useEffect } from "react";
import { submitQuery, ApiError } from "./api";
import ChatWindow from "./components/ChatWindow";
import QueryInput from "./components/QueryInput";
import ErrorBanner from "./components/ErrorBanner";
import styles from "./styles/App.module.css";

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources?: string[];
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSubmit(queryText: string) {
    setError(null);

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      text: queryText,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await submitQuery(queryText);
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: response.response_text,
        sources: response.sources.length > 0 ? response.sources : undefined,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <svg
          className={styles.logo}
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect width="64" height="64" rx="14" fill="#0f1729" />
          <rect
            x="2"
            y="2"
            width="60"
            height="60"
            rx="12"
            fill="none"
            stroke="url(#hBolt)"
            strokeWidth="1.5"
            opacity="0.4"
          />
          <path
            d="M38 14 L18 36 L28 36 L26 50 L46 28 L36 28 Z"
            fill="url(#hBolt)"
          />
          <defs>
            <linearGradient
              id="hBolt"
              x1="20%"
              y1="0%"
              x2="80%"
              y2="100%"
            >
              <stop offset="0%" stopColor="#00f0ff" />
              <stop offset="100%" stopColor="#f5a623" />
            </linearGradient>
          </defs>
        </svg>
        <div className={styles.headerText}>
          <h1>ZEPP</h1>
          <span className={styles.headerSubtitle}>Knowledge Engine</span>
        </div>
        <div className={styles.headerStatus}>
          <span className={styles.statusDot} />
          Online
        </div>
      </header>

      <main className={styles.main}>
        {error && (
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        )}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          bottomRef={bottomRef}
          onPromptClick={handleSubmit}
        />
      </main>

      <footer className={styles.footer}>
        <QueryInput onSubmit={handleSubmit} isLoading={isLoading} />
      </footer>
    </div>
  );
}
