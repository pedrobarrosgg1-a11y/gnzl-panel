import { useSystemConfig } from "../hooks/useSystemConfig";
import styles from "./DemoBadge.module.css";

/**
 * Sinaliza a origem dos dados no cabeçalho. O modo demo precisa ficar
 * visível em toda tela para não confundir dado fictício com dado real.
 */
export function DemoBadge() {
  const { status, config } = useSystemConfig();

  if (status === "loading") {
    return (
      <span className="gz-badge" role="status">
        <span className={`gz-ping gz-ping--pulse ${styles.ping}`} aria-hidden="true" />
        conectando
      </span>
    );
  }

  if (status === "error" || !config) {
    return (
      <span className="gz-badge">
        <span className={`gz-ping ${styles.ping}`} aria-hidden="true" />
        api offline
      </span>
    );
  }

  return (
    <span className="gz-badge">
      <span className={`gz-ping ${styles.ping}`} aria-hidden="true" />
      {config.is_demo ? "modo demo" : "shopee"}
    </span>
  );
}
