import type { ReactNode } from "react";

import styles from "./StateMessage.module.css";

interface StateMessageProps {
  tone: "loading" | "error";
  title?: string;
  description: string;
  action?: ReactNode;
}

/**
 * Estado de carregamento ou erro com a mesma leitura visual da busca.
 * Carregando usa o ping pulsante; erro usa o ping estático e um CTA.
 */
export function StateMessage({
  tone,
  title,
  description,
  action,
}: StateMessageProps) {
  return (
    <div
      className={styles.state}
      role={tone === "error" ? "alert" : "status"}
    >
      <span
        className={`gz-ping ${tone === "loading" ? "gz-ping--pulse" : ""} ${styles.ping}`}
        aria-hidden="true"
      />
      {title ? <h2 className={styles.title}>{title}</h2> : null}
      <p className={styles.text}>{description}</p>
      {action ? <div className={styles.action}>{action}</div> : null}
    </div>
  );
}
