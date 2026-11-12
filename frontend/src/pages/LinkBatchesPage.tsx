import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";

import { DemoBadge } from "../components/DemoBadge";
import { EmptyState } from "../components/EmptyState";
import { Feedback } from "../components/Feedback";
import { FormPanel } from "../components/FormPanel";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StateMessage } from "../components/StateMessage";
import { StatusBadge } from "../components/StatusBadge";
import { api, isAbortError, toApiError, type ApiError } from "../services/api";
import type {
  LinkBatchInput,
  LinkBatchListResponse,
  Product,
  ProductListSummary,
} from "../types/api";
import { formatDateTime } from "../utils/datetime";
import {
  BATCH_STATUS_LABELS,
  BATCH_STATUS_OPTIONS,
  SOURCE_OPTIONS,
  batchOriginLabel,
  batchResultLabel,
  isBatchStatus,
  isDataSource,
  parsePositiveInt,
  parseProductIds,
} from "../utils/links";
import { formatInteger } from "../utils/money";
import styles from "./LinkBatchesPage.module.css";

const PAGE_SIZE = 20;

type BatchesState =
  | { status: "loading" }
  | { status: "ready"; data: LinkBatchListResponse }
  | { status: "error"; error: ApiError };

type ListsState =
  | { status: "loading" }
  | { status: "ready"; lists: ProductListSummary[] }
  | { status: "error"; error: ApiError };

interface BatchFormValues {
  name: string;
  listId: string;
  observation: string;
  subId1: string;
  subId2: string;
  subId3: string;
  subId4: string;
  subId5: string;
}

interface FormErrors {
  listId?: string;
}

type FeedbackState = {
  tone: "success" | "error" | "info";
  message: string;
};

const EMPTY_FORM: BatchFormValues = {
  name: "",
  listId: "",
  observation: "",
  subId1: "",
  subId2: "",
  subId3: "",
  subId4: "",
  subId5: "",
};

function parseFilters(paramsKey: string) {
  const params = new URLSearchParams(paramsKey);
  const status = params.get("status");
  const source = params.get("source");
  return {
    status: isBatchStatus(status) ? status : undefined,
    source: isDataSource(source) ? source : undefined,
    page: Math.max(1, Number(params.get("page")) || 1),
  };
}

export function LinkBatchesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const paramsKey = searchParams.toString();
  const navigate = useNavigate();
  const location = useLocation();

  const filters = useMemo(() => parseFilters(paramsKey), [paramsKey]);
  const creation = useMemo(() => {
    const params = new URLSearchParams(paramsKey);
    return {
      productMode: params.has("produtos"),
      productIds: parseProductIds(params.get("produtos")),
      prefillListId: parsePositiveInt(params.get("lista")),
    };
  }, [paramsKey]);

  const selectedProducts = useMemo<Product[]>(() => {
    const state = location.state as { products?: Product[] } | null;
    return Array.isArray(state?.products) ? state.products : [];
  }, [location.state]);

  const hasFilters = Boolean(filters.status || filters.source);

  const [batches, setBatches] = useState<BatchesState>({ status: "loading" });
  const [retryToken, setRetryToken] = useState(0);
  const [lists, setLists] = useState<ListsState>({ status: "loading" });
  const [listsRetryToken, setListsRetryToken] = useState(0);
  const [form, setForm] = useState<BatchFormValues>(EMPTY_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [creating, setCreating] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);

  const nameId = useId();
  const listId = useId();
  const observationId = useId();
  const statusId = useId();
  const sourceId = useId();
  const nameRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLSelectElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    setBatches({ status: "loading" });

    api
      .getLinkBatches(
        {
          status: filters.status,
          source: filters.source,
          page: filters.page,
          page_size: PAGE_SIZE,
        },
        { signal: controller.signal },
      )
      .then((data) => setBatches({ status: "ready", data }))
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setBatches({ status: "error", error: toApiError(cause) });
      });

    return () => controller.abort();
  }, [filters, retryToken]);

  useEffect(() => {
    const controller = new AbortController();
    setLists({ status: "loading" });

    api
      .getLists({ signal: controller.signal })
      .then((items) => setLists({ status: "ready", lists: items }))
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setLists({ status: "error", error: toApiError(cause) });
      });

    return () => controller.abort();
  }, [listsRetryToken]);

  useEffect(() => {
    if (creation.prefillListId === null) {
      return;
    }
    setForm((current) => ({
      ...current,
      listId: String(creation.prefillListId),
    }));
  }, [creation.prefillListId]);

  function updateField<K extends keyof BatchFormValues>(
    key: K,
    value: BatchFormValues[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateFilter(key: "status" | "source", value: string) {
    const next = new URLSearchParams(paramsKey);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    next.delete("page");
    setSearchParams(next);
  }

  function clearFilters() {
    const next = new URLSearchParams(paramsKey);
    next.delete("status");
    next.delete("source");
    next.delete("page");
    setSearchParams(next);
  }

  function goToPage(page: number) {
    const next = new URLSearchParams(paramsKey);
    next.set("page", String(page));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function resetForm() {
    setForm({
      ...EMPTY_FORM,
      listId:
        creation.prefillListId !== null ? String(creation.prefillListId) : "",
    });
    setErrors({});
    setFeedback(null);
  }

  function leaveProductMode() {
    const next = new URLSearchParams(paramsKey);
    next.delete("produtos");
    next.delete("page");
    setSearchParams(next, { replace: true, state: null });
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors({});
    setFeedback(null);

    const subIds = {
      sub_id_1: form.subId1.trim() || null,
      sub_id_2: form.subId2.trim() || null,
      sub_id_3: form.subId3.trim() || null,
      sub_id_4: form.subId4.trim() || null,
      sub_id_5: form.subId5.trim() || null,
    };

    let input: LinkBatchInput;
    if (creation.productMode) {
      if (creation.productIds.length === 0) {
        setFeedback({
          tone: "error",
          message: "selecione ao menos um produto na busca para criar o lote.",
        });
        return;
      }
      input = {
        name: form.name.trim() || null,
        destination_type: "product",
        product_ids: creation.productIds,
        product_list_id: null,
        observation: form.observation.trim() || null,
        ...subIds,
      };
    } else {
      const parsedListId = Number(form.listId);
      if (!Number.isInteger(parsedListId) || parsedListId <= 0) {
        setErrors({ listId: "escolha a lista que vai originar o lote." });
        listRef.current?.focus();
        return;
      }
      input = {
        name: form.name.trim() || null,
        destination_type: "list",
        product_ids: [],
        product_list_id: parsedListId,
        observation: form.observation.trim() || null,
        ...subIds,
      };
    }

    setCreating(true);
    try {
      const created = await api.createLinkBatch(input);
      navigate(`/lotes/${created.id}`, { state: { created: true } });
    } catch (cause: unknown) {
      setFeedback({ tone: "error", message: toApiError(cause).message });
    } finally {
      setCreating(false);
    }
  }

  const listsReady = lists.status === "ready" ? lists.lists : null;
  const prefillMissing =
    creation.prefillListId !== null &&
    listsReady !== null &&
    !listsReady.some((item) => item.id === creation.prefillListId);

  const nameField = (
    <div className="gz-field">
      <label className="gz-label" htmlFor={nameId}>
        nome do lote
      </label>
      <input
        ref={nameRef}
        id={nameId}
        className="gz-input"
        type="text"
        value={form.name}
        onChange={(event: ChangeEvent<HTMLInputElement>) =>
          updateField("name", event.target.value)
        }
        maxLength={160}
        placeholder="black friday, stories de verão…"
      />
      <p className="gz-field-note">opcional.</p>
    </div>
  );

  return (
    <>
      <PageHeader
        eyebrow="lotes"
        title="lotes de links"
        description="gere links em lote a partir de uma lista ou de produtos escolhidos na busca. cada lote guarda os sub ids e o resultado item a item."
        actions={<DemoBadge />}
      />

      <form className={styles.form} onSubmit={handleCreate} noValidate>
        <FormPanel
          title="novo lote"
          description="os sub ids valem para todos os links do lote. a geração acontece no detalhe, depois de revisar os itens."
          footer={
            <>
              <button
                type="submit"
                className="gz-btn gz-btn--primary"
                disabled={
                  creating ||
                  (creation.productMode && creation.productIds.length === 0)
                }
              >
                {creating ? "criando…" : "criar lote"}
              </button>
              <button
                type="button"
                className="gz-btn gz-btn--ghost"
                onClick={resetForm}
                disabled={creating}
              >
                limpar
              </button>
            </>
          }
        >
          {creation.productMode ? (
            <>
              <section
                className={styles.originSummary}
                aria-label="produtos selecionados para o lote"
              >
                <div className={styles.originText}>
                  <span className="gz-label">origem · produtos da busca</span>
                  <p className={styles.originTitle}>
                    {creation.productIds.length}{" "}
                    {creation.productIds.length === 1
                      ? "produto selecionado"
                      : "produtos selecionados"}
                  </p>
                  {selectedProducts.length > 0 ? (
                    <ul className={styles.productList}>
                      {selectedProducts.slice(0, 6).map((product) => (
                        <li key={product.id}>{product.title}</li>
                      ))}
                      {selectedProducts.length > 6 ? (
                        <li>+ {selectedProducts.length - 6} outros</li>
                      ) : null}
                    </ul>
                  ) : (
                    <p className={styles.note}>
                      a lista completa aparece no detalhe do lote depois da
                      criação.
                    </p>
                  )}
                </div>
                <div className={styles.originActions}>
                  <Link className="gz-btn gz-btn--outline gz-btn--small" to="/">
                    trocar seleção
                  </Link>
                  <button
                    type="button"
                    className="gz-btn gz-btn--ghost gz-btn--small"
                    onClick={leaveProductMode}
                  >
                    usar uma lista
                  </button>
                </div>
              </section>
              {nameField}
            </>
          ) : (
            <>
              <div className={styles.fields}>
                {nameField}

                <div className="gz-field">
                  <label className="gz-label" htmlFor={listId}>
                    lista de origem
                  </label>
                  <select
                    ref={listRef}
                    id={listId}
                    className="gz-input"
                    value={form.listId}
                    onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                      updateField("listId", event.target.value)
                    }
                    disabled={lists.status !== "ready"}
                    aria-invalid={Boolean(errors.listId)}
                    aria-describedby={
                      errors.listId ? `${listId}-error` : undefined
                    }
                  >
                    <option value="">selecione uma lista</option>
                    {listsReady?.map((item) => (
                      <option key={item.id} value={String(item.id)}>
                        {item.name} · {item.item_count}{" "}
                        {item.item_count === 1 ? "produto" : "produtos"}
                      </option>
                    ))}
                  </select>
                  {errors.listId ? (
                    <p className="gz-field-error" id={`${listId}-error`}>
                      {errors.listId}
                    </p>
                  ) : null}
                  {lists.status === "loading" ? (
                    <p className="gz-field-note">carregando listas…</p>
                  ) : null}
                  {lists.status === "error" ? (
                    <p className="gz-field-note">
                      listas indisponíveis.{" "}
                      <button
                        type="button"
                        className={styles.inlineButton}
                        onClick={() => setListsRetryToken((value) => value + 1)}
                      >
                        tentar novamente
                      </button>
                    </p>
                  ) : null}
                  {listsReady && listsReady.length === 0 ? (
                    <p className="gz-field-note">
                      nenhuma lista criada.{" "}
                      <Link className={styles.inlineLink} to="/listas">
                        criar uma lista
                      </Link>
                    </p>
                  ) : null}
                  {prefillMissing ? (
                    <p className="gz-field-note">
                      a lista indicada não existe mais. escolha outra.
                    </p>
                  ) : null}
                </div>
              </div>

              <p className={styles.note}>
                para produtos avulsos, use{" "}
                <strong>selecionar produtos</strong> na busca e crie o lote a
                partir da seleção.
              </p>
            </>
          )}

          <div className="gz-field">
            <label className="gz-label" htmlFor={observationId}>
              observação
            </label>
            <textarea
              id={observationId}
              className={`gz-input ${styles.textarea}`}
              value={form.observation}
              onChange={(event: ChangeEvent<HTMLTextAreaElement>) =>
                updateField("observation", event.target.value)
              }
              maxLength={2000}
              rows={2}
              placeholder="o que este lote divulga?"
            />
          </div>

          <fieldset className={styles.subIds}>
            <legend className="gz-label">sub ids</legend>
            <p className={styles.note}>
              opcionais. a mesma combinação é aplicada a todos os links do lote e
              vai para o relatório da shopee.
            </p>
            <div className={styles.subIdGrid}>
              {(
                [
                  ["subId1", "sub id 1"],
                  ["subId2", "sub id 2"],
                  ["subId3", "sub id 3"],
                  ["subId4", "sub id 4"],
                  ["subId5", "sub id 5"],
                ] as const
              ).map(([key, label]) => (
                <div className="gz-field" key={key}>
                  <label className="gz-label" htmlFor={`${key}-${nameId}`}>
                    {label}
                  </label>
                  <input
                    id={`${key}-${nameId}`}
                    className="gz-input"
                    type="text"
                    value={form[key]}
                    onChange={(event: ChangeEvent<HTMLInputElement>) =>
                      updateField(key, event.target.value)
                    }
                    maxLength={64}
                    placeholder="campanha"
                    autoComplete="off"
                  />
                </div>
              ))}
            </div>
          </fieldset>
        </FormPanel>
      </form>

      {feedback ? (
        <div className={styles.feedback}>
          <Feedback tone={feedback.tone}>{feedback.message}</Feedback>
        </div>
      ) : null}

      <section className={styles.section} aria-label="lotes criados">
        <div className={styles.filters}>
          <div className={styles.filterField}>
            <label className="gz-label" htmlFor={statusId}>
              status
            </label>
            <select
              id={statusId}
              className="gz-input"
              value={filters.status ?? ""}
              onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                updateFilter("status", event.target.value)
              }
            >
              <option value="">todos</option>
              {BATCH_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.filterField}>
            <label className="gz-label" htmlFor={sourceId}>
              origem
            </label>
            <select
              id={sourceId}
              className="gz-input"
              value={filters.source ?? ""}
              onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                updateFilter("source", event.target.value)
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

          {hasFilters ? (
            <button
              type="button"
              className={`gz-btn gz-btn--ghost gz-btn--small ${styles.clearFilters}`}
              onClick={clearFilters}
            >
              limpar filtros
            </button>
          ) : null}
        </div>

        {batches.status === "loading" ? (
          <StateMessage tone="loading" description="carregando os lotes…" />
        ) : null}

        {batches.status === "error" ? (
          <StateMessage
            tone="error"
            title="não foi possível carregar os lotes"
            description={batches.error.message}
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

        {batches.status === "ready" ? (
          batches.data.items.length === 0 ? (
            hasFilters ? (
              <EmptyState
                title="nenhum lote encontrado"
                description="nenhum lote corresponde a esses filtros. remova o status ou a origem para ver todos."
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
                title="nenhum lote ainda"
                description="crie um lote a partir de uma lista ou de produtos escolhidos na busca. os links só são gerados quando você pedir."
                action={
                  <button
                    type="button"
                    className="gz-btn gz-btn--primary"
                    onClick={() => nameRef.current?.focus()}
                  >
                    criar primeiro lote
                  </button>
                }
              />
            )
          ) : (
            <>
              <div className={styles.meta}>
                <span className="gz-label">lotes recentes</span>
                <span className={styles.count}>
                  {formatInteger(batches.data.total)}{" "}
                  {batches.data.total === 1 ? "lote" : "lotes"}
                </span>
              </div>

              <div className={styles.tableWrap}>
                <table className="gz-table">
                  <caption className="gz-visually-hidden">
                    lotes de geração de links com origem, status e data
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">lote</th>
                      <th scope="col">origem</th>
                      <th scope="col" className="gz-num">
                        itens
                      </th>
                      <th scope="col">status</th>
                      <th scope="col" className="gz-num">
                        criado em
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {batches.data.items.map((batch) => (
                      <tr key={batch.id}>
                        <td>
                          <Link
                            className={styles.batchLink}
                            to={`/lotes/${batch.id}`}
                          >
                            {batch.name ?? `lote #${batch.id}`}
                          </Link>
                          <span className={styles.rowMeta}>
                            #{batch.id} ·{" "}
                            {batch.is_demo ? "demo" : batch.source}
                          </span>
                        </td>
                        <td className={styles.origin}>
                          {batchOriginLabel(batch)}
                        </td>
                        <td className="gz-num">
                          {formatInteger(batch.total_items)}
                        </td>
                        <td>
                          <StatusBadge
                            label={BATCH_STATUS_LABELS[batch.status]}
                            live={batch.status === "running"}
                          />
                          <span className={styles.rowMeta}>
                            {batchResultLabel(batch)}
                          </span>
                        </td>
                        <td className="gz-num">
                          {formatDateTime(batch.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Pagination
                page={batches.data.page}
                hasNext={batches.data.has_next}
                onPrevious={() => goToPage(batches.data.page - 1)}
                onNext={() => goToPage(batches.data.page + 1)}
              />
            </>
          )
        ) : null}
      </section>
    </>
  );
}
