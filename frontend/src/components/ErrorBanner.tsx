import styles from "../styles/ErrorBanner.module.css";

interface Props {
  message: string;
  onDismiss: () => void;
}

export default function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div className={styles.banner} role="alert">
      <span className={styles.message}>{message}</span>
      <button
        className={styles.dismiss}
        onClick={onDismiss}
        aria-label="Dismiss error"
      >
        &times;
      </button>
    </div>
  );
}
