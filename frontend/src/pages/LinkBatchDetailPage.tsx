import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { DemoBadge } from "../components/DemoBadge";
import { Feedback } from "../components/Feedback";
import { PageHeader } from "../components/PageHeader";
import { StateMessage } from "../components/StateMessage";
import { StatusBadge } from "../components/StatusBadge";
import {
  ArrowUpRightIcon,
  ChevronLeftIcon,
  CopyIcon,
} from "../components/icons";
import {
  ApiError,
  api,
  isAbortError,
  toApiError,
} from "../services/api";
import type { LinkBatchDetail, LinkBatchItem } from "../types/api";
import { copyToClipboard } from "../utils/clipboard";
import { formatDateTime } from "../utils/datetime";
import {
  BATCH_ITEM_STATUS_LABELS,
  BATCH_STATUS_LABELS,
  batchOriginLabel,
  formatSubIds,
} from "../utils/links";
import { formatInteger } from "../utils/money";
import styles from "./LinkBatchDetailPage.module.css";

type DetailState =
  | { status: "loading" }
  | { status: "ready"; detail: LinkBatchDetail }
  | { status: "error"; error: ApiError };

type FeedbackState = {
  tone: "success" | "error" | "info";
  message: string;
};

function runResultMessage(detail: LinkBatchDetail): FeedbackState {
  if (detail.status === "completed") {
    return {
      tone: "success",
      message: `${detail.successful_items} ${
        detail.successful_items === 1 ? "link gerado" : "links gerados"
      }.`,
    };
  }
  if (detail.status === "partial") {
    return {
      tone: "info",
      message: `${detail.successful_items} ${
        detail.successful_items === 1 ? "link gerado" : "links gerados"
      } e ${detail.failed_items} com falha. tente novamente os itens pendentes.`,
    };
  }
  return {
    tone: "error",
    message:
      "nenhum link foi gerado. veja o motivo em cada item antes de tentar novamente.",
  };
}

function canRun(detail: LinkBatchDetail): boolean {
  return (
    detail.status === "pending" ||
    detail.status === "partial" ||
    detail.status === "failed"
  );
}

export function LinkBatchDetailPage() {
  const { batchId: batchIdParam } = useParams();
  const parsedId = Number(batchIdParam);
  const batchId =
    Number.isInteger(parsedId) && parsedId > 0 ? parsedId : null;

  const [state, setState] = useState<DetailState>(() =>
    batchId === null
      ? {
          status: "error",
          error: new ApiError("not_found", "Lote não encontrado.", 404),
        }
      : { status: "loading" },
  );
  const [retryToken, setRetryToken] = useState(0);
  const [running, setRunning] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);

  useEffect(() => {
    setFeedback(null);
  }, [batchId]);

  useEffect(() => {
    if (batchId === null) {
      return;
    }

    const controller = new AbortController();
    setState({ status: "loading" });

    api
      .getLinkBatch(batchId, { signal: controller.signal })
      .then((detail) => setState({ status: "ready", detail }))
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setState({ status: "error", error: toApiError(cause) });
      });

    return () => controller.abort();
  }, [batchId, retryToken]);

  async function handleRun(detail: LinkBatchDetail) {
    setRunning(true);
    setFeedback({ tone: "info", message: "gerando os links do lote…" });

    try {
      const updated = await api.runLinkBatch(detail.id);
      setState({ status: "ready", detail: updated });
      setFeedback(runResultMessage(updated));
    } catch (cause: unknown) {
      setFeedback({ tone: "error", message: toApiError(cause).message });
      setRetryToken((value) => value + 1);
    } finally {
      setRunning(false);
    }
  }

  async function handleCopy(item: LinkBatchItem) {
    if (!item.affiliate_url) {
      return;
    }
    const title = item.product?.title ?? "produto";
    const copied = await copyToClipboard(item.affiliate_url);
    setFeedback(
      copied
        ? { tone: "success", message: `link de "${title}" copiado.` }
        : {
            tone: "error",
            message:
              "não foi possível copiar o link. abra-o e copie a url manualmente.",
          },
    );
  }

  const detail = state.status === "ready" ? state.detail : null;
  const notFound = state.status === "error" && state.error.status === 404;
  const subIds = detail ? formatSubIds(detail) : "—";
  const runnable = detail ? canRun(detail) : false;

  return (
    <>
      <Link className={styles.back} to="/lotes">
        <ChevronLeftIcon className={styles.backIcon} />
        lotes
      </Link>

      <PageHeader
        eyebrow="lote"
        title={
          detail
            ? detail.name ?? `lote #${detail.id}`
            : batchId
              ? `lote #${batchId}`
              : "lote"
        }
        description={
          detail
            ? detail.observation ??
              "revise os itens e gere os links. o resultado de cada produto fica nesta página."
            : undefined
        }
        actions={
          <>
            <DemoBadge />
            {detail ? (
              <StatusBadge
                label={BATCH_STATUS_LABELS[detail.status]}
                live={running || detail.status === "running"}
              />
            ) : null}
            {detail && runnable ? (
              <button
                type="button"
                className="gz-btn gz-btn--primary"
                onClick={() => handleRun(detail)}
                disabled={running}
              >
                {running
                  ? "gerando links…"
                  : detail.status === "pending"
                    ? "gerar links"
                    : "tentar pendentes"}
              </button>
            ) : null}
            {detail && detail.status === "running" && !running ? (
              <button
                type="button"
                className="gz-btn gz-btn--outline"
                onClick={() => setRetryToken((value) => value + 1)}
              >
                atualizar
              </button>
            ) : null}
            {detail && detail.successful_items > 0 ? (
              <Link
                className="gz-btn gz-btn--outline"
                to={`/links?batch_id=${detail.id}`}
              >
                ver links
              </Link>
            ) : null}
          </>
        }
      />

      {state.status === "loading" ? (
        <StateMessage tone="loading" description="carregando o lote…" />
      ) : null}

      {state.status === "error" ? (
        <StateMessage
          tone="error"
          title={
            notFound
              ? "lote não encontrado"
              : "não foi possível carregar o lote"
          }
          description={
            notFound
              ? "esse lote pode ter sido removido. volte para lotes para ver o que continua disponível."
              : state.error.message
          }
          action={
            <div className={styles.stateActions}>
              <Link className="gz-btn gz-btn--primary" to="/lotes">
                voltar para lotes
              </Link>
              {notFound ? null : (
                <button
                  type="button"
                  className="gz-btn gz-btn--outline"
                  onClick={() => setRetryToken((value) => value + 1)}
                >
                  tentar novamente
                </button>
              )}
            </div>
          }
        />
      ) : null}

      {detail ? (
        <>
          <dl className={styles.metaBand}>
            <div className={styles.metric}>
              <dt className="gz-label">itens</dt>
              <dd className={styles.metricValue}>
                {formatInteger(detail.total_items)}
              </dd>
            </div>
            <div className={styles.metric}>
              <dt className="gz-label">links gerados</dt>
              <dd className={styles.metricValue}>
                {formatInteger(detail.successful_items)}
              </dd>
            </div>
            <div className={styles.metric}>
              <dt className="gz-label">falhas</dt>
              <dd className={styles.metricValue}>
                {formatInteger(detail.failed_items)}
              </dd>
            </div>
            <div className={styles.metric}>
              <dt className="gz-label">criado em</dt>
              <dd className={styles.metricDate}>
                {formatDateTime(detail.created_at)}
              </dd>
            </div>
          </dl>

          <dl className={styles.details}>
            <div>
              <dt className="gz-label">origem</dt>
              <dd>{batchOriginLabel(detail)}</dd>
            </div>
            <div>
              <dt className="gz-label">sub ids</dt>
              <dd>{subIds}</dd>
            </div>
            <div>
              <dt className="gz-label">finalizado</dt>
              <dd>
                {detail.finished_at
                  ? formatDateTime(detail.finished_at)
                  : "ainda não"}
              </dd>
            </div>
          </dl>

          {detail.status === "pending" ? (
            <div className={styles.notice}>
              <Feedback tone="info">
                lote criado com {detail.total_items}{" "}
                {detail.total_items === 1 ? "item" : "itens"}. os links ainda
                não foram gerados.
              </Feedback>
            </div>
          ) : null}

          {detail.status === "running" && !running ? (
            <div className={styles.notice}>
              <Feedback tone="info">
                o lote está em execução. atualize para ver o progresso.
              </Feedback>
            </div>
          ) : null}

          {feedback ? (
            <div className={styles.feedback}>
              <Feedback tone={feedback.tone}>{feedback.message}</Feedback>
            </div>
          ) : null}

          <section className={styles.items} aria-label="itens do lote">
            <div className={styles.itemsHead}>
              <span className="gz-label">itens do lote</span>
              <span className={styles.count}>
                {detail.items.length}{" "}
                {detail.items.length === 1 ? "item" : "itens"}
              </span>
            </div>

            <div className={styles.tableWrap}>
              <table className="gz-table">
                <caption className="gz-visually-hidden">
                  itens do lote com produto, status, link gerado e tentativas
                </caption>
                <thead>
                  <tr>
                    <th scope="col">produto</th>
                    <th scope="col">status</th>
                    <th scope="col">resultado</th>
                    <th scope="col" className="gz-num">
                      tentativas
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {detail.items.map((item) => {
                    const title = item.product?.title ?? "produto não identificado";
                    return (
                      <tr key={item.id}>
                        <td>
                          <span className={styles.productTitle}>{title}</span>
                          <span className={styles.productMeta}>
                            {item.product
                              ? `item ${item.product.item_id} · loja ${item.product.shop_id}`
                              : item.original_url}
                          </span>
                        </td>
                        <td>
                          <StatusBadge
                            label={BATCH_ITEM_STATUS_LABELS[item.status]}
                          />
                        </td>
                        <td>
                          {item.status === "success" && item.affiliate_url ? (
                            <div className={styles.result}>
                              <span
                                className={styles.url}
                                title={item.affiliate_url}
                              >
                                {item.affiliate_url}
                              </span>
                              <div className={styles.resultActions}>
                                <button
                                  type="button"
                                  className="gz-icon-btn"
                                  onClick={() => handleCopy(item)}
                                  aria-label={`copiar link de "${title}"`}
                                >
                                  <CopyIcon />
                                </button>
                                <a
                                  className="gz-icon-btn"
                                  href={item.affiliate_url}
                                  target="_blank"
                                  rel="noreferrer noopener"
                                  aria-label={`abrir link de "${title}"`}
                                >
                                  <ArrowUpRightIcon />
                                </a>
                              </div>
                            </div>
                          ) : null}

                          {item.status === "failed" ? (
                            <div className={styles.result}>
                              <span className={styles.failure}>
                                {item.error_message ??
                                  "falha ao gerar o link."}
                              </span>
                              {item.error_code ? (
                                <span className={styles.errorCode}>
                                  {item.error_code}
                                </span>
                              ) : null}
                            </div>
                          ) : null}

                          {item.status === "pending" ? (
                            <span className={styles.muted}>
                              aguardando execução.
                            </span>
                          ) : null}
                          {item.status === "skipped" ? (
                            <span className={styles.muted}>ignorado.</span>
                          ) : null}
                        </td>
                        <td className="gz-num">
                          {formatInteger(item.attempts)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : null}
    </>
  );
}
