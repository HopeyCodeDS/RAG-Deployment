import styles from "../styles/LoadingBubble.module.css";

export default function LoadingBubble() {
  return (
    <div className={styles.row} aria-label="Waiting for response">
      <div className={styles.bubble}>
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
      </div>
    </div>
  );
}
