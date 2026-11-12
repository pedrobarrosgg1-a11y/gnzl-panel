import styles from "./StatusBadge.module.css";

interface StatusBadgeProps {
  label: string;
  /** Anima o ping apenas quando o status está em andamento. */
  live?: boolean;
}

/**
 * Selo de status sempre com texto: a cor sozinha nunca comunica o estado.
 */
export function StatusBadge({ label, live = false }: StatusBadgeProps) {
  return (
    <span className={`gz-badge ${styles.badge}`}>
      <span
        className={`gz-ping ${live ? "gz-ping--pulse" : ""} ${styles.ping}`}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}
