import { Link } from "react-router";

import styles from "./Brand.module.css";

interface BrandProps {
  /** Fecha o menu móvel ao navegar. */
  onNavigate?: () => void;
}

export function Brand({ onNavigate }: BrandProps) {
  return (
    <Link to="/" className={styles.brand} onClick={onNavigate}>
      <span className={styles.name}>
        gnzl
        <span className={`gz-ping ${styles.ping}`} aria-hidden="true" />
      </span>
      <span className={styles.sub}>achados</span>
      <span className="gz-visually-hidden">— ir para a busca</span>
    </Link>
  );
}
