import { useId, type ReactNode } from "react";

import styles from "./FormPanel.module.css";

interface FormPanelProps {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
}

/**
 * Área de formulário com título próprio. Borda fina separa a criação de
 * lista do restante da página sem transformar o bloco em card.
 */
export function FormPanel({
  title,
  description,
  children,
  footer,
}: FormPanelProps) {
  const titleId = useId();

  return (
    <section className={styles.panel} aria-labelledby={titleId}>
      <header className={styles.header}>
        <h2 className={styles.title} id={titleId}>
          {title}
        </h2>
        {description ? (
          <p className={styles.description}>{description}</p>
        ) : null}
      </header>
      <div className={styles.body}>{children}</div>
      {footer ? <div className={styles.footer}>{footer}</div> : null}
    </section>
  );
}
