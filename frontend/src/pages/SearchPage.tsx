import {
  useEffect,
  useId,
  useMemo,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { DemoBadge } from "../components/DemoBadge";
import { EmptyState } from "../components/EmptyState";
import { Feedback } from "../components/Feedback";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { ProductTable } from "../components/ProductTable";
import { CheckIcon, PlusIcon, SearchIcon } from "../components/icons";
import { api, isAbortError, toApiError, type ApiError } from "../services/api";
import type {
  Product,
  ProductListDetail,
  ProductSearchResponse,
} from "../types/api";
import {
  EMPTY_SEARCH_FORM,
  SORT_OPTIONS,
  buildSearch,
  formValuesFromParams,
  paramsFromValues,
  queryFromParams,
  type SearchFormErrors,
  type SearchFormValues,
} from "../utils/search";
import styles from "./SearchPage.module.css";

const MAX_SELECTED_PRODUCTS = 200;

type ResultsState =
  | { status: "loading" }
  | { status: "ready"; data: ProductSearchResponse }
  | { status: "error"; error: ApiError };

type TargetListState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; list: ProductListDetail }
  | { status: "error"; error: ApiError };

interface ListFeedback {
  tone: "success" | "error" | "info";
  message: string;
}

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const paramsKey = searchParams.toString();

  const searchId = useId();
  const categoryId = useId();
  const sortId = useId();
  const priceMinId = useId();
  const priceMaxId = useId();
  const commissionId = useId();

  const [form, setForm] = useState<SearchFormValues>(() =>
    formValuesFromParams(new URLSearchParams(paramsKey)),
  );
  const [errors, setErrors] = useState<SearchFormErrors>({});
  const [categories, setCategories] = useState<string[]>([]);
  const [categoriesFailed, setCategoriesFailed] = useState(false);
  const [results, setResults] = useState<ResultsState>({ status: "loading" });
  const [retryToken, setRetryToken] = useState(0);
  const [targetList, setTargetList] = useState<TargetListState>({
    status: "idle",
  });
  const [listRetryToken, setListRetryToken] = useState(0);
  const [addingId, setAddingId] = useState<number | null>(null);
  const [listFeedback, setListFeedback] = useState<ListFeedback | null>(null);
  const [selecting, setSelecting] = useState(false);
  const [selected, setSelected] = useState<Map<number, Product>>(
    () => new Map(),
  );

  const params = useMemo(() => new URLSearchParams(paramsKey), [paramsKey]);
  const query = useMemo(() => queryFromParams(params), [params]);
  const listId = useMemo(() => {
    const raw = params.get("lista");
    if (!raw) {
      return null;
    }
    const value = Number(raw);
    return Number.isInteger(value) && value > 0 ? value : null;
  }, [params]);
  const listProductIds = useMemo(
    () =>
      new Set(
        targetList.status === "ready"
          ? targetList.list.items.map((item) => item.id)
          : [],
      ),
    [targetList],
  );

  // A URL é a fonte da verdade: voltar/avançar no navegador repõe o formulário.
  useEffect(() => {
    setForm(formValuesFromParams(new URLSearchParams(paramsKey)));
    setErrors({});
  }, [paramsKey]);

  useEffect(() => {
    const controller = new AbortController();
    api
      .getCategories({ signal: controller.signal })
      .then((response) => {
        setCategories(response.items);
        setCategoriesFailed(false);
      })
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setCategoriesFailed(true);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setResults({ status: "loading" });

    api
      .searchProducts(query, { signal: controller.signal })
      .then((data) => setResults({ status: "ready", data }))
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setResults({ status: "error", error: toApiError(cause) });
      });

    return () => controller.abort();
  }, [query, retryToken]);

  useEffect(() => {
    if (listId === null) {
      setTargetList({ status: "idle" });
      setListFeedback(null);
      setAddingId(null);
      return;
    }

    const controller = new AbortController();
    setTargetList({ status: "loading" });
    setListFeedback(null);

    api
      .getList(listId, { signal: controller.signal })
      .then((list) => setTargetList({ status: "ready", list }))
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setTargetList({ status: "error", error: toApiError(cause) });
      });

    return () => controller.abort();
  }, [listId, listRetryToken]);

  function updateField<K extends keyof SearchFormValues>(
    key: K,
    value: SearchFormValues[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const { query: built, errors: nextErrors } = buildSearch(form);
    if (!built) {
      setErrors(nextErrors);
      return;
    }
    setErrors({});
    setSelected(new Map());
    setSearchParams(withListParam(paramsFromValues(form)));
  }

  function handleClear() {
    setForm(EMPTY_SEARCH_FORM);
    setErrors({});
    setSelected(new Map());
    setSearchParams(withListParam(new URLSearchParams()));
  }

  function withListParam(next: URLSearchParams): URLSearchParams {
    if (listId !== null) {
      next.set("lista", String(listId));
    }
    return next;
  }

  function leaveListMode() {
    const next = new URLSearchParams(paramsKey);
    next.delete("lista");
    setSearchParams(next);
  }

  function goToPage(nextPage: number) {
    const next = new URLSearchParams(paramsKey);
    next.set("page", String(nextPage));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleAddToList(product: Product) {
    if (targetList.status !== "ready" || addingId !== null) {
      return;
    }

    const list = targetList.list;
    setAddingId(product.id);
    setListFeedback(null);

    try {
      const result = await api.addListItems(list.id, [product.id]);
      setTargetList({
        status: "ready",
        list: {
          ...list,
          item_count: result.item_count,
          items: result.items,
        },
      });
      setListFeedback(
        result.added === 0
          ? {
              tone: "info",
              message: `"${product.title}" já estava nesta lista.`,
            }
          : {
              tone: "success",
              message: `"${product.title}" adicionado a "${list.name}".`,
            },
      );
    } catch (cause: unknown) {
      setListFeedback({ tone: "error", message: toApiError(cause).message });
    } finally {
      setAddingId(null);
    }
  }

  function toggleSelected(product: Product) {
    setSelected((current) => {
      const next = new Map(current);
      if (next.has(product.id)) {
        next.delete(product.id);
        return next;
      }
      if (next.size >= MAX_SELECTED_PRODUCTS) {
        return current;
      }
      next.set(product.id, product);
      return next;
    });
  }

  function exitSelection() {
    setSelected(new Map());
    setSelecting(false);
  }

  function createBatchFromSelection() {
    if (selected.size === 0) {
      return;
    }
    const products = [...selected.values()];
    navigate(`/lotes?produtos=${products.map((item) => item.id).join(",")}`, {
      state: { products },
    });
  }

  const categoryField = (
    <div className={styles.field}>
      <label className="gz-label" htmlFor={categoryId}>
        categoria
      </label>
      <select
        id={categoryId}
        className="gz-input"
        value={form.category}
        onChange={(event: ChangeEvent<HTMLSelectElement>) =>
          updateField("category", event.target.value)
        }
      >
        <option value="">todas</option>
        {categories.map((category) => (
          <option key={category} value={category}>
            {category}
          </option>
        ))}
      </select>
      {categoriesFailed ? (
        <p className={styles.fieldNote}>categorias indisponíveis.</p>
      ) : null}
    </div>
  );

  return (
    <>
      <PageHeader
        eyebrow="busca"
        title="o que vamos achar hoje?"
        description="produtos da shopee com preço, comissão e vendas. o ponto de partida para escolher o que divulgar."
        actions={<DemoBadge />}
      />

      {listId !== null ? (
        <section
          className={styles.listBanner}
          aria-label="modo de adicionar produtos à lista"
          role={targetList.status === "error" ? "alert" : undefined}
        >
          <div className={styles.listBannerText}>
            <span className="gz-label">adicionando a</span>
            <p className={styles.listBannerTitle}>
              {targetList.status === "ready"
                ? targetList.list.name
                : targetList.status === "error"
                  ? "lista indisponível"
                  : "abrindo lista…"}
            </p>
            <p className={styles.listBannerNote}>
              {targetList.status === "ready"
                ? `${targetList.list.item_count} ${
                    targetList.list.item_count === 1 ? "produto" : "produtos"
                  } na lista. use o botão + para incluir um resultado.`
                : targetList.status === "error"
                  ? targetList.error.message
                  : "carregando os produtos que já estão na lista."}
            </p>
          </div>
          <div className={styles.listBannerActions}>
            {targetList.status === "ready" ? (
              <Link
                className="gz-btn gz-btn--outline gz-btn--small"
                to={`/listas/${targetList.list.id}`}
              >
                ver lista
              </Link>
            ) : null}
            {targetList.status === "error" ? (
              <button
                type="button"
                className="gz-btn gz-btn--outline gz-btn--small"
                onClick={() => setListRetryToken((value) => value + 1)}
              >
                tentar novamente
              </button>
            ) : null}
            <button
              type="button"
              className="gz-btn gz-btn--ghost gz-btn--small"
              onClick={leaveListMode}
            >
              sair
            </button>
          </div>
        </section>
      ) : null}

      {listFeedback ? (
        <div className={styles.listFeedback}>
          <Feedback tone={listFeedback.tone}>{listFeedback.message}</Feedback>
        </div>
      ) : null}

      <form
        className={styles.form}
        onSubmit={handleSubmit}
        role="search"
        aria-label="busca de produtos"
        noValidate
      >
        <div className={styles.searchRow}>
          <div className={styles.searchField}>
            <SearchIcon className={styles.searchIcon} />
            <label className="gz-visually-hidden" htmlFor={searchId}>
              buscar produtos
            </label>
            <input
              id={searchId}
              className={`gz-input gz-input--pill ${styles.searchInput}`}
              type="search"
              placeholder="o que vamos achar hoje?"
              value={form.q}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                updateField("q", event.target.value)
              }
              maxLength={120}
              autoComplete="off"
            />
          </div>
          <button
            type="submit"
            className={`gz-btn gz-btn--primary ${styles.submit}`}
          >
            buscar
          </button>
        </div>

        <div className={styles.filters}>
          {categoryField}

          <div className={styles.field}>
            <label className="gz-label" htmlFor={sortId}>
              ordenar por
            </label>
            <select
              id={sortId}
              className="gz-input"
              value={form.sort}
              onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                updateField("sort", event.target.value as SearchFormValues["sort"])
              }
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.field}>
            <label className="gz-label" htmlFor={priceMinId}>
              preço mínimo
            </label>
            <input
              id={priceMinId}
              className="gz-input"
              inputMode="decimal"
              placeholder="R$ 0,00"
              value={form.priceMin}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                updateField("priceMin", event.target.value)
              }
              aria-invalid={Boolean(errors.priceMin)}
              aria-describedby={
                errors.priceMin ? `${priceMinId}-error` : undefined
              }
            />
            {errors.priceMin ? (
              <p className={styles.fieldError} id={`${priceMinId}-error`}>
                {errors.priceMin}
              </p>
            ) : null}
          </div>

          <div className={styles.field}>
            <label className="gz-label" htmlFor={priceMaxId}>
              preço máximo
            </label>
            <input
              id={priceMaxId}
              className="gz-input"
              inputMode="decimal"
              placeholder="R$ 0,00"
              value={form.priceMax}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                updateField("priceMax", event.target.value)
              }
              aria-invalid={Boolean(errors.priceMax)}
              aria-describedby={
                errors.priceMax ? `${priceMaxId}-error` : undefined
              }
            />
            {errors.priceMax ? (
              <p className={styles.fieldError} id={`${priceMaxId}-error`}>
                {errors.priceMax}
              </p>
            ) : null}
          </div>

          <div className={styles.field}>
            <label className="gz-label" htmlFor={commissionId}>
              comissão mínima
            </label>
            <input
              id={commissionId}
              className="gz-input"
              inputMode="decimal"
              placeholder="0%"
              value={form.commissionMin}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                updateField("commissionMin", event.target.value)
              }
              aria-invalid={Boolean(errors.commissionMin)}
              aria-describedby={
                errors.commissionMin ? `${commissionId}-error` : undefined
              }
            />
            {errors.commissionMin ? (
              <p className={styles.fieldError} id={`${commissionId}-error`}>
                {errors.commissionMin}
              </p>
            ) : null}
          </div>

          <button
            type="button"
            className={`gz-btn gz-btn--ghost gz-btn--small ${styles.clear}`}
            onClick={handleClear}
          >
            limpar filtros
          </button>
        </div>

        {errors.range ? (
          <p className={styles.formError} role="alert">
            {errors.range}
          </p>
        ) : null}
      </form>

      <section className={styles.results} aria-label="resultados da busca">
        {results.status === "loading" ? (
          <div className={styles.state} role="status">
            <span
              className={`gz-ping gz-ping--pulse ${styles.statePing}`}
              aria-hidden="true"
            />
            <p className={styles.stateText}>buscando produtos…</p>
          </div>
        ) : null}

        {results.status === "error" ? (
          <div className={styles.state} role="alert">
            <span className={`gz-ping ${styles.statePing}`} aria-hidden="true" />
            <h2 className={styles.stateTitle}>não foi possível buscar</h2>
            <p className={styles.stateText}>{results.error.message}</p>
            <button
              type="button"
              className="gz-btn gz-btn--primary"
              onClick={() => setRetryToken((value) => value + 1)}
            >
              tentar novamente
            </button>
          </div>
        ) : null}

        {results.status === "ready" ? (
          results.data.items.length === 0 ? (
            <EmptyState
              title="nada encontrado"
              description="nenhum produto corresponde a esses filtros. ajuste o termo, a faixa de preço ou a comissão mínima."
              action={
                <button
                  type="button"
                  className="gz-btn gz-btn--primary"
                  onClick={handleClear}
                >
                  limpar filtros
                </button>
              }
            />
          ) : (
            <>
              <div className={styles.meta}>
                <div>
                  <span className="gz-label">resultados</span>
                  <p className={styles.count}>
                    {results.data.total === null
                      ? `${results.data.items.length} nesta página`
                      : `${results.data.total} ${
                          results.data.total === 1 ? "achado" : "achados"
                        }`}
                  </p>
                </div>
                <div className={styles.metaSide}>
                  <p className={styles.metaNote}>
                    {results.data.is_demo
                      ? "dados fictícios do modo demo"
                      : "dados da shopee"}
                  </p>
                  {listId === null ? (
                    <button
                      type="button"
                      className="gz-btn gz-btn--outline gz-btn--small"
                      onClick={() => {
                        if (selecting) {
                          exitSelection();
                        } else {
                          setSelecting(true);
                        }
                      }}
                    >
                      {selecting ? "sair da seleção" : "selecionar produtos"}
                    </button>
                  ) : null}
                </div>
              </div>

              {selecting && listId === null ? (
                <section
                  className={styles.selectionBar}
                  aria-label="seleção de produtos para o lote"
                >
                  <div className={styles.selectionText}>
                    <span className="gz-label">seleção</span>
                    <p className={styles.selectionCount}>
                      {selected.size}{" "}
                      {selected.size === 1 ? "produto selecionado" : "produtos selecionados"}
                    </p>
                    <p className={styles.selectionNote}>
                      marque os produtos que vão entrar no lote. o limite é de{" "}
                      {MAX_SELECTED_PRODUCTS} itens por lote.
                    </p>
                  </div>
                  <div className={styles.selectionActions}>
                    <button
                      type="button"
                      className="gz-btn gz-btn--primary gz-btn--small"
                      onClick={createBatchFromSelection}
                      disabled={selected.size === 0}
                    >
                      criar lote com {selected.size}{" "}
                      {selected.size === 1 ? "produto" : "produtos"}
                    </button>
                    <button
                      type="button"
                      className="gz-btn gz-btn--ghost gz-btn--small"
                      onClick={() => setSelected(new Map())}
                      disabled={selected.size === 0}
                    >
                      limpar seleção
                    </button>
                  </div>
                </section>
              ) : null}

              <ProductTable
                products={results.data.items}
                caption={
                  listId !== null
                    ? "resultados da busca para adicionar à lista"
                    : selecting
                      ? "resultados da busca para selecionar produtos do lote"
                      : undefined
                }
                selectable={selecting && listId === null}
                selectedIds={new Set(selected.keys())}
                onToggleSelect={toggleSelected}
                selectionLimitReached={
                  selected.size >= MAX_SELECTED_PRODUCTS
                }
                actionsLabel="adicionar à lista"
                actions={
                  listId !== null
                    ? (product) => {
                        if (targetList.status !== "ready") {
                          return (
                            <button
                              type="button"
                              className="gz-icon-btn"
                              disabled
                              aria-label={
                                targetList.status === "error"
                                  ? `"${product.title}" não pode ser adicionado: lista indisponível`
                                  : `"${product.title}" aguardando a lista carregar`
                              }
                            >
                              <PlusIcon />
                            </button>
                          );
                        }

                        if (listProductIds.has(product.id)) {
                          return (
                            <button
                              type="button"
                              className={styles.listAction}
                              disabled
                              aria-label={`"${product.title}" já está na lista`}
                            >
                              <CheckIcon aria-hidden="true" />
                              na lista
                            </button>
                          );
                        }

                        const busy = addingId === product.id;
                        return (
                          <button
                            type="button"
                            className="gz-icon-btn"
                            onClick={() => handleAddToList(product)}
                            disabled={addingId !== null}
                            aria-busy={busy}
                            aria-label={
                              busy
                                ? `adicionando "${product.title}" à lista`
                                : `adicionar "${product.title}" à lista "${targetList.list.name}"`
                            }
                          >
                            {busy ? (
                              <span
                                className="gz-ping gz-ping--pulse"
                                aria-hidden="true"
                              />
                            ) : (
                              <PlusIcon />
                            )}
                          </button>
                        );
                      }
                    : undefined
                }
              />

              <Pagination
                page={results.data.page}
                hasNext={results.data.has_next}
                onPrevious={() => goToPage(results.data.page - 1)}
                onNext={() => goToPage(results.data.page + 1)}
              />
            </>
          )
        ) : null}
      </section>
    </>
  );
}
