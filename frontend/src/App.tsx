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
        <h1>Zepp</h1>
      </header>

      <main className={styles.main}>
        {error && (
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        )}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          bottomRef={bottomRef}
        />
      </main>

      <footer className={styles.footer}>
        <QueryInput onSubmit={handleSubmit} isLoading={isLoading} />
      </footer>
    </div>
  );
}
