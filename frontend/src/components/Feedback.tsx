import type { ReactNode } from "react";

import styles from "./Feedback.module.css";

interface FeedbackProps {
  tone: "success" | "error" | "info";
  children: ReactNode;
}

/**
 * Confirmação breve, sem modal. Erros usam role="alert"; o restante é
 * anunciado como status para leitores de tela.
 */
export function Feedback({ tone, children }: FeedbackProps) {
  return (
    <p
      className={`${styles.feedback} ${styles[tone]}`}
      role={tone === "error" ? "alert" : "status"}
    >
      {children}
    </p>
  );
}
