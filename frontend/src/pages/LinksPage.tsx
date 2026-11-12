import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { Link, useSearchParams } from "react-router";

import { DemoBadge } from "../components/DemoBadge";
import { EmptyState } from "../components/EmptyState";
import { Feedback } from "../components/Feedback";
import { FormPanel } from "../components/FormPanel";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StateMessage } from "../components/StateMessage";
import { StatusBadge } from "../components/StatusBadge";
import {
  ArrowUpRightIcon,
  CopyIcon,
  SearchIcon,
} from "../components/icons";
import { api, isAbortError, toApiError, type ApiError } from "../services/api";
import type {
  AffiliateLink,
  DataSource,
  LinkBatchSummary,
  LinkListResponse,
  LinkQuery,
  LinkStatus,
} from "../types/api";
import { copyToClipboard } from "../utils/clipboard";
import { formatDateTime } from "../utils/datetime";
import {
  LINK_STATUS_LABELS,
  LINK_STATUS_OPTIONS,
  SOURCE_OPTIONS,
  formatSubIds,
  isDataSource,
  isLinkStatus,
  normalizeSubIdInput,
  parsePositiveInt,
  sameSubIds,
  subIdValues,
} from "../utils/links";
import { formatInteger } from "../utils/money";
import styles from "./LinksPage.module.css";

const PAGE_SIZE = 20;

type LinksState =
  | { status: "loading" }
  | { status: "ready"; data: LinkListResponse }
  | { status: "error"; error: ApiError };

type BatchOptionsState =
  | { status: "loading" }
  | { status: "ready"; items: LinkBatchSummary[] }
  | { status: "error" };

type FeedbackState = {
  tone: "success" | "error" | "info";
  message: string;
};

interface FilterFormValues {
  q: string;
  batchId: string;
  status: LinkStatus | "";
  source: DataSource | "";
  subId1: string;
  subId2: string;
  subId3: string;
}

interface FilterErrors {
  subId1?: string;
  subId2?: string;
  subId3?: string;
}

interface RegenerateValues {
  subId1: string;
  subId2: string;
  subId3: string;
  subId4: string;
  subId5: string;
  observation: string;
}

const EMPTY_FILTERS: FilterFormValues = {
  q: "",
  batchId: "",
  status: "",
  source: "",
  subId1: "",
  subId2: "",
  subId3: "",
};

const EMPTY_REGENERATE: RegenerateValues = {
  subId1: "",
  subId2: "",
  subId3: "",
  subId4: "",
  subId5: "",
  observation: "",
};

const FILTER_KEYS = [
  "q",
  "batch_id",
  "status",
  "source",
  "sub_id_1",
  "sub_id_2",
  "sub_id_3",
] as const;

function formFromParams(params: URLSearchParams): FilterFormValues {
  const status = params.get("status");
  const source = params.get("source");
  return {
    q: params.get("q") ?? "",
    batchId: params.get("batch_id") ?? "",
    status: isLinkStatus(status) ? status : "",
    source: isDataSource(source) ? source : "",
    subId1: params.get("sub_id_1") ?? "",
    subId2: params.get("sub_id_2") ?? "",
    subId3: params.get("sub_id_3") ?? "",
  };
}

function queryFromParams(params: URLSearchParams): LinkQuery {
  const q = params.get("q")?.trim();
  const status = params.get("status");
  const source = params.get("source");
  const batchId = parsePositiveInt(params.get("batch_id"));
  return {
    q: q || undefined,
    batch_id: batchId ?? undefined,
    status: isLinkStatus(status) ? status : undefined,
    source: isDataSource(source) ? source : undefined,
    sub_id_1: normalizeSubIdInput(params.get("sub_id_1") ?? "") ?? undefined,
    sub_id_2: normalizeSubIdInput(params.get("sub_id_2") ?? "") ?? undefined,
    sub_id_3: normalizeSubIdInput(params.get("sub_id_3") ?? "") ?? undefined,
    page: Math.max(1, Number(params.get("page")) || 1),
    page_size: PAGE_SIZE,
  };
}

export function LinksPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const paramsKey = searchParams.toString();
  const query = useMemo(
    () => queryFromParams(new URLSearchParams(paramsKey)),
    [paramsKey],
  );
  const activeFilters = useMemo(() => {
    const params = new URLSearchParams(paramsKey);
    return FILTER_KEYS.some((key) => Boolean(params.get(key)));
  }, [paramsKey]);

  const [state, setState] = useState<LinksState>({ status: "loading" });
  const [retryToken, setRetryToken] = useState(0);
  const [batchOptions, setBatchOptions] = useState<BatchOptionsState>({
    status: "loading",
  });
  const [form, setForm] = useState<FilterFormValues>(() =>
    formFromParams(new URLSearchParams(paramsKey)),
  );
  const [errors, setErrors] = useState<FilterErrors>({});
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);

  const [regenerating, setRegenerating] = useState<AffiliateLink | null>(null);
  const [regenerateValues, setRegenerateValues] =
    useState<RegenerateValues>(EMPTY_REGENERATE);
  const [regenerateError, setRegenerateError] = useState<string | null>(null);
  const [regenerateBusy, setRegenerateBusy] = useState(false);

  const searchId = useId();
  const batchId = useId();
  const statusId = useId();
  const sourceId = useId();
  const subId1 = useId();
  const subId2 = useId();
  const subId3 = useId();
  const regenerateBase = useId();
  const regenerateFirstRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setForm(formFromParams(new URLSearchParams(paramsKey)));
    setErrors({});
  }, [paramsKey]);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });

    api
      .getLinks(query, { signal: controller.signal })
      .then((data) => setState({ status: "ready", data }))
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setState({ status: "error", error: toApiError(cause) });
      });

    return () => controller.abort();
  }, [query, retryToken]);

  useEffect(() => {
    const controller = new AbortController();

    api
      .getLinkBatches({ page_size: 100 }, { signal: controller.signal })
      .then((data) =>
        setBatchOptions({ status: "ready", items: data.items }),
      )
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setBatchOptions({ status: "error" });
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (regenerating) {
      regenerateFirstRef.current?.focus();
    }
  }, [regenerating]);

  function updateField<K extends keyof FilterFormValues>(
    key: K,
    value: FilterFormValues[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handleFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: FilterErrors = {};
    const normalizedSubIds = [
      form.subId1,
      form.subId2,
      form.subId3,
    ].map((value, index) => {
      const normalized = normalizeSubIdInput(value);
      if (value.trim() && normalized === null) {
        const key = `subId${index + 1}` as keyof FilterErrors;
        nextErrors[key] = "use letras, números e hífen.";
      }
      return normalized;
    });

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setErrors({});
    const next = new URLSearchParams();
    const q = form.q.trim();
    if (q) next.set("q", q);
    if (form.batchId) next.set("batch_id", form.batchId);
    if (form.status) next.set("status", form.status);
    if (form.source) next.set("source", form.source);
    normalizedSubIds.forEach((value, index) => {
      if (value) next.set(`sub_id_${index + 1}`, value);
    });
    next.set("page", "1");
    setSearchParams(next);
  }

  function clearFilters() {
    setForm(EMPTY_FILTERS);
    setErrors({});
    setSearchParams(new URLSearchParams());
  }

  function goToPage(page: number) {
    const next = new URLSearchParams(paramsKey);
    next.set("page", String(page));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleCopy(link: AffiliateLink) {
    const title = link.product?.title ?? "produto";
    const copied = await copyToClipboard(link.affiliate_url);
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

  function startRegenerate(link: AffiliateLink) {
    setRegenerating(link);
    setRegenerateValues({
      subId1: link.sub_id_1 ?? "",
      subId2: link.sub_id_2 ?? "",
      subId3: link.sub_id_3 ?? "",
      subId4: link.sub_id_4 ?? "",
      subId5: link.sub_id_5 ?? "",
      observation: link.observation ?? "",
    });
    setRegenerateError(null);
    setFeedback(null);
  }

  function cancelRegenerate() {
    setRegenerating(null);
    setRegenerateError(null);
  }

  async function handleRegenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!regenerating) {
      return;
    }

    const nextSubIds = [
      normalizeSubIdInput(regenerateValues.subId1),
      normalizeSubIdInput(regenerateValues.subId2),
      normalizeSubIdInput(regenerateValues.subId3),
      normalizeSubIdInput(regenerateValues.subId4),
      normalizeSubIdInput(regenerateValues.subId5),
    ];

    if (sameSubIds(nextSubIds, subIdValues(regenerating))) {
      setRegenerateError(
        "altere ao menos um sub id para gerar uma url diferente.",
      );
      regenerateFirstRef.current?.focus();
      return;
    }

    setRegenerateBusy(true);
    setRegenerateError(null);

    try {
      const created = await api.regenerateLink(regenerating.id, {
        sub_id_1: nextSubIds[0],
        sub_id_2: nextSubIds[1],
        sub_id_3: nextSubIds[2],
        sub_id_4: nextSubIds[3],
        sub_id_5: nextSubIds[4],
        observation: regenerateValues.observation.trim() || null,
      });
      setRegenerating(null);
      setFeedback({
        tone: "success",
        message: `novo link #${created.id} gerado. o link anterior foi marcado como substituído.`,
      });
      const reset = new URLSearchParams(paramsKey);
      reset.set("page", "1");
      setSearchParams(reset, { replace: true });
      setRetryToken((value) => value + 1);
    } catch (cause: unknown) {
      setRegenerateError(toApiError(cause).message);
    } finally {
      setRegenerateBusy(false);
    }
  }

  const batchItems =
    batchOptions.status === "ready" ? batchOptions.items : [];
  const missingBatch =
    form.batchId &&
    (batchOptions.status !== "ready" ||
      !batchItems.some((item) => String(item.id) === form.batchId))
      ? form.batchId
      : null;
  const linkCount = state.status === "ready" ? state.data.total : 0;

  return (
    <>
      <PageHeader
        eyebrow="links"
        title="histórico de links"
        description="cada link gerado fica registrado com produto, lote, sub ids e data. links regenerados mantêm o anterior no histórico."
        actions={
          <>
            <DemoBadge />
            <Link className="gz-btn gz-btn--primary" to="/lotes">
              criar lote
            </Link>
          </>
        }
      />

      <form
        className={styles.filters}
        onSubmit={handleFilterSubmit}
        role="search"
        aria-label="filtros do histórico de links"
        noValidate
      >
        <div className={`${styles.field} ${styles.searchField}`}>
          <label className="gz-visually-hidden" htmlFor={searchId}>
            buscar links
          </label>
          <SearchIcon className={styles.searchIcon} />
          <input
            id={searchId}
            className={`gz-input ${styles.searchInput}`}
            type="search"
            placeholder="produto ou url"
            value={form.q}
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              updateField("q", event.target.value)
            }
            maxLength={200}
            autoComplete="off"
          />
        </div>

        <div className={styles.field}>
          <label className="gz-label" htmlFor={batchId}>
            lote
          </label>
          <select
            id={batchId}
            className="gz-input"
            value={form.batchId}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              updateField("batchId", event.target.value)
            }
          >
            <option value="">todos os lotes</option>
            {missingBatch ? (
              <option value={missingBatch}>lote #{missingBatch}</option>
            ) : null}
            {batchItems.map((item) => (
              <option key={item.id} value={String(item.id)}>
                {item.name ?? `lote #${item.id}`} · #{item.id}
              </option>
            ))}
          </select>
          {batchOptions.status === "error" ? (
            <p className={styles.fieldNote}>
              lista de lotes indisponível; o filtro por número continua valendo.
            </p>
          ) : null}
        </div>

        <div className={styles.field}>
          <label className="gz-label" htmlFor={statusId}>
            status
          </label>
          <select
            id={statusId}
            className="gz-input"
            value={form.status}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              updateField("status", event.target.value as LinkStatus | "")
            }
          >
            <option value="">todos</option>
            {LINK_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.field}>
          <label className="gz-label" htmlFor={sourceId}>
            origem
          </label>
          <select
            id={sourceId}
            className="gz-input"
            value={form.source}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              updateField("source", event.target.value as DataSource | "")
            }
          >
            <option value="">todas</option>
            {SOURCE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {(
          [
            [subId1, "subId1", "sub id 1", "campanha"],
            [subId2, "subId2", "sub id 2", "canal"],
            [subId3, "subId3", "sub id 3", "formato"],
          ] as const
        ).map(([id, key, label, placeholder]) => (
          <div className={styles.field} key={key}>
            <label className="gz-label" htmlFor={id}>
              {label}
            </label>
            <input
              id={id}
              className="gz-input"
              type="text"
              value={form[key]}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                updateField(key, event.target.value)
              }
              maxLength={64}
              placeholder={placeholder}
              autoComplete="off"
              aria-invalid={Boolean(errors[key])}
              aria-describedby={errors[key] ? `${id}-error` : undefined}
            />
            {errors[key] ? (
              <p className="gz-field-error" id={`${id}-error`}>
                {errors[key]}
              </p>
            ) : null}
          </div>
        ))}

        <div className={styles.filterActions}>
          <button type="submit" className="gz-btn gz-btn--primary gz-btn--small">
            filtrar
          </button>
          <button
            type="button"
            className="gz-btn gz-btn--ghost gz-btn--small"
            onClick={clearFilters}
          >
            limpar filtros
          </button>
        </div>
      </form>

      {feedback ? (
        <div className={styles.feedback}>
          <Feedback tone={feedback.tone}>{feedback.message}</Feedback>
        </div>
      ) : null}

      {regenerating ? (
        <div className={styles.regenerate}>
          <form onSubmit={handleRegenerate} noValidate>
            <FormPanel
              title={`regenerar link #${regenerating.id}`}
              description={`novo link para "${
                regenerating.product?.title ?? "produto"
              }". o link atual continua no histórico como substituído.`}
              footer={
                <>
                  <button
                    type="submit"
                    className="gz-btn gz-btn--primary"
                    disabled={regenerateBusy}
                  >
                    {regenerateBusy ? "regenerando…" : "regenerar link"}
                  </button>
                  <button
                    type="button"
                    className="gz-btn gz-btn--ghost"
                    onClick={cancelRegenerate}
                    disabled={regenerateBusy}
                  >
                    cancelar
                  </button>
                </>
              }
            >
              <p className={styles.regenerateNote}>
                sub ids atuais: {formatSubIds(regenerating)}. altere ao menos um
                para gerar uma url diferente.
              </p>

              <div className={styles.subIdGrid}>
                {(
                  [
                    ["subId1", "sub id 1", true],
                    ["subId2", "sub id 2", false],
                    ["subId3", "sub id 3", false],
                    ["subId4", "sub id 4", false],
                    ["subId5", "sub id 5", false],
                  ] as const
                ).map(([key, label, isFirst]) => (
                  <div className="gz-field" key={key}>
                    <label
                      className="gz-label"
                      htmlFor={`${regenerateBase}-${key}`}
                    >
                      {label}
                    </label>
                    <input
                      ref={isFirst ? regenerateFirstRef : undefined}
                      id={`${regenerateBase}-${key}`}
                      className="gz-input"
                      type="text"
                      value={regenerateValues[key]}
                      onChange={(event: ChangeEvent<HTMLInputElement>) =>
                        setRegenerateValues((current) => ({
                          ...current,
                          [key]: event.target.value,
                        }))
                      }
                      maxLength={64}
                      autoComplete="off"
                    />
                  </div>
                ))}
              </div>

              <div className="gz-field">
                <label
                  className="gz-label"
                  htmlFor={`${regenerateBase}-observation`}
                >
                  observação
                </label>
                <textarea
                  id={`${regenerateBase}-observation`}
                  className={`gz-input ${styles.textarea}`}
                  value={regenerateValues.observation}
                  onChange={(event: ChangeEvent<HTMLTextAreaElement>) =>
                    setRegenerateValues((current) => ({
                      ...current,
                      observation: event.target.value,
                    }))
                  }
                  maxLength={2000}
                  rows={2}
                />
              </div>

              {regenerateError ? (
                <Feedback tone="error">{regenerateError}</Feedback>
              ) : null}
            </FormPanel>
          </form>
        </div>
      ) : null}

      <section className={styles.results} aria-label="links gerados">
        {state.status === "loading" ? (
          <StateMessage tone="loading" description="carregando os links…" />
        ) : null}

        {state.status === "error" ? (
          <StateMessage
            tone="error"
            title="não foi possível carregar os links"
            description={state.error.message}
            action={
              <button
                type="button"
                className="gz-btn gz-btn--primary"
                onClick={() => setRetryToken((value) => value + 1)}
              >
                tentar novamente
              </button>
            }
          />
        ) : null}

        {state.status === "ready" ? (
          state.data.items.length === 0 ? (
            activeFilters ? (
              <EmptyState
                title="nada encontrado"
                description="nenhum link corresponde a esses filtros. ajuste o termo, o lote ou os sub ids."
                action={
                  <button
                    type="button"
                    className="gz-btn gz-btn--primary"
                    onClick={clearFilters}
                  >
                    limpar filtros
                  </button>
                }
              />
            ) : (
              <EmptyState
                title="nenhum link gerado"
                description="crie um lote a partir de uma lista e gere os links. cada link aparece aqui com sub ids, status e data."
                action={
                  <Link className="gz-btn gz-btn--primary" to="/lotes">
                    criar um lote
                  </Link>
                }
              />
            )
          ) : (
            <>
              <div className={styles.meta}>
                <span className="gz-label">links gerados</span>
                <span className={styles.count}>
                  {formatInteger(linkCount)}{" "}
                  {linkCount === 1 ? "link" : "links"}
                </span>
              </div>

              <div className={styles.tableWrap}>
                <table className="gz-table">
                  <caption className="gz-visually-hidden">
                    links de afiliado com produto, sub ids, status e data
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">produto</th>
                      <th scope="col">link</th>
                      <th scope="col">sub ids</th>
                      <th scope="col">status</th>
                      <th scope="col" className="gz-num">
                        criado em
                      </th>
                      <th scope="col">
                        <span className="gz-visually-hidden">ações</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {state.data.items.map((link) => {
                      const title =
                        link.product?.title ?? "produto não identificado";
                      return (
                        <tr key={link.id}>
                          <td>
                            <span className={styles.productTitle}>{title}</span>
                            <span className={styles.productMeta}>
                              link #{link.id} ·{" "}
                              {link.link_batch_id ? (
                                <Link
                                  className={styles.inlineLink}
                                  to={`/lotes/${link.link_batch_id}`}
                                >
                                  lote #{link.link_batch_id}
                                </Link>
                              ) : (
                                "sem lote"
                              )}{" "}
                              · {link.is_demo ? "demo" : link.source}
                            </span>
                          </td>
                          <td>
                            <span
                              className={styles.url}
                              title={link.affiliate_url}
                            >
                              {link.affiliate_url}
                            </span>
                            {link.status === "replaced" &&
                            link.replaced_by_id ? (
                              <span className={styles.rowMeta}>
                                substituído pelo link #{link.replaced_by_id}
                              </span>
                            ) : null}
                          </td>
                          <td className={styles.subIdsCell}>
                            {formatSubIds(link)}
                          </td>
                          <td>
                            <StatusBadge
                              label={LINK_STATUS_LABELS[link.status]}
                            />
                          </td>
                          <td className="gz-num">
                            {formatDateTime(link.created_at)}
                          </td>
                          <td className={styles.actionsCell}>
                            <button
                              type="button"
                              className="gz-icon-btn"
                              onClick={() => handleCopy(link)}
                              aria-label={`copiar link de "${title}"`}
                            >
                              <CopyIcon />
                            </button>
                            <a
                              className="gz-icon-btn"
                              href={link.affiliate_url}
                              target="_blank"
                              rel="noreferrer noopener"
                              aria-label={`abrir link de "${title}"`}
                            >
                              <ArrowUpRightIcon />
                            </a>
                            {link.status === "active" ? (
                              <button
                                type="button"
                                className="gz-btn gz-btn--ghost gz-btn--small"
                                onClick={() => startRegenerate(link)}
                                aria-label={`regenerar link de "${title}"`}
                              >
                                regenerar
                              </button>
                            ) : null}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <Pagination
                page={state.data.page}
                hasNext={state.data.has_next}
                onPrevious={() => goToPage(state.data.page - 1)}
                onNext={() => goToPage(state.data.page + 1)}
              />
            </>
          )
        ) : null}
      </section>
    </>
  );
}
