import { ChevronLeftIcon, ChevronRightIcon } from "./icons";
import styles from "./Pagination.module.css";

interface PaginationProps {
  page: number;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
}

export function Pagination({
  page,
  hasNext,
  onPrevious,
  onNext,
}: PaginationProps) {
  return (
    <nav className={styles.bar} aria-label="paginação dos resultados">
      <span className={styles.page}>página {page}</span>
      <div className={styles.controls}>
        <button
          type="button"
          className="gz-btn gz-btn--outline gz-btn--small"
          onClick={onPrevious}
          disabled={page <= 1}
        >
          <ChevronLeftIcon className={styles.icon} />
          anterior
        </button>
        <button
          type="button"
          className="gz-btn gz-btn--outline gz-btn--small"
          onClick={onNext}
          disabled={!hasNext}
        >
          próxima
          <ChevronRightIcon className={styles.icon} />
        </button>
      </div>
    </nav>
  );
}
