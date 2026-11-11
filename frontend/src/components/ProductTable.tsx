import type { ReactNode } from "react";

import type { Product } from "../types/api";
import {
  formatBRL,
  formatInteger,
  formatPercentFromBp,
  formatRating,
} from "../utils/money";
import { ArrowUpRightIcon } from "./icons";
import styles from "./ProductTable.module.css";

interface ProductTableProps {
  products: Product[];
  caption?: string;
  actionsLabel?: string;
  actions?: (product: Product) => ReactNode;
}

export function ProductTable({
  products,
  caption = "resultados da busca de produtos",
  actionsLabel = "ações",
  actions,
}: ProductTableProps) {
  return (
    <div className={styles.wrap}>
      <table
        className={`gz-table ${styles.table} ${actions ? styles.tableWithActions : ""}`}
      >
        <caption className="gz-visually-hidden">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">produto</th>
            <th scope="col">categoria</th>
            <th scope="col" className="gz-num">
              preço
            </th>
            <th scope="col" className="gz-num">
              comissão
            </th>
            <th scope="col" className="gz-num">
              vendas
            </th>
            <th scope="col" className="gz-num">
              avaliação
            </th>
            <th scope="col">
              <span className="gz-visually-hidden">link do produto</span>
            </th>
            {actions ? (
              <th scope="col">
                <span className="gz-visually-hidden">{actionsLabel}</span>
              </th>
            ) : null}
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.id}>
              <td>
                <div className={styles.product}>
                  <div className={styles.thumb} aria-hidden="true">
                    {product.image_url ? (
                      <img
                        src={product.image_url}
                        alt=""
                        loading="lazy"
                        width={44}
                        height={44}
                      />
                    ) : (
                      <span>{product.title.charAt(0)}</span>
                    )}
                  </div>
                  <div className={styles.info}>
                    <span className={styles.title}>{product.title}</span>
                    <span className={styles.meta}>
                      item {product.item_id} · loja {product.shop_id}
                    </span>
                  </div>
                </div>
              </td>
              <td className={styles.category}>{product.category ?? "—"}</td>
              <td className="gz-num">{formatBRL(product.price_cents)}</td>
              <td className="gz-num">
                {formatPercentFromBp(product.commission_rate_bp)}
              </td>
              <td className="gz-num">{formatInteger(product.sales)}</td>
              <td className="gz-num">{formatRating(product.rating_x100)}</td>
              <td className={styles.linkCell}>
                {product.product_url ? (
                  <a
                    className={styles.external}
                    href={product.product_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    aria-label={`abrir "${product.title}" na shopee`}
                  >
                    <ArrowUpRightIcon className={styles.icon} />
                  </a>
                ) : (
                  <span className={styles.noLink}>—</span>
                )}
              </td>
              {actions ? (
                <td className={styles.actionsCell}>{actions(product)}</td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
