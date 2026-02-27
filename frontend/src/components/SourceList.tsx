import styles from "../styles/SourceList.module.css";

interface Props {
  sources: string[];
}

export default function SourceList({ sources }: Props) {
  return (
    <div className={styles.container}>
      <p className={styles.label}>Sources</p>
      <ul className={styles.list}>
        {sources.map((src, i) => (
          <li key={i}>
            <span className={styles.chip}>{src}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
