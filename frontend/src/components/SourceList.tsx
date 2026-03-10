import { API_BASE } from "../api";
import styles from "../styles/SourceList.module.css";

interface Props {
  sources: string[];
}

/** Parse "galaxy-design-client-guide.pdf:3:1" into { filename, page, label } */
function parseSource(sourceId: string) {
  const parts = sourceId.split(":");
  if (parts.length >= 2) {
    const filename = parts.slice(0, -2).join(":");
    const page = parts[parts.length - 2];
    return {
      filename,
      page: parseInt(page, 10),
      label: `${filename} — p.${page}`,
    };
  }
  return { filename: sourceId, page: null, label: sourceId };
}

/** Deduplicate by filename+page (multiple chunks from same page). */
function deduplicateSources(sources: string[]) {
  const seen = new Set<string>();
  const result: ReturnType<typeof parseSource>[] = [];
  for (const src of sources) {
    const parsed = parseSource(src);
    const key = `${parsed.filename}:${parsed.page}`;
    if (!seen.has(key)) {
      seen.add(key);
      result.push(parsed);
    }
  }
  return result;
}

export default function SourceList({ sources }: Props) {
  const parsed = deduplicateSources(sources);

  return (
    <div className={styles.container}>
      <p className={styles.label}>
        <svg
          className={styles.labelIcon}
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zM14 2v6h6" />
        </svg>
        Sources
      </p>
      <ul className={styles.list}>
        {parsed.map((src, i) => {
          const url =
            API_BASE && src.page !== null
              ? `${API_BASE}/documents/${encodeURIComponent(src.filename)}#page=${src.page}`
              : undefined;

          return (
            <li key={i}>
              {url ? (
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.chip}
                >
                  <svg
                    className={styles.chipIcon}
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" />
                  </svg>
                  {src.label}
                </a>
              ) : (
                <span className={styles.chip}>{src.label}</span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
