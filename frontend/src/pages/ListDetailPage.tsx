import {
  useEffect,
  useId,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { Link, useNavigate, useParams } from "react-router";

import { DemoBadge } from "../components/DemoBadge";
import { EmptyState } from "../components/EmptyState";
import { Feedback } from "../components/Feedback";
import { FormPanel } from "../components/FormPanel";
import { PageHeader } from "../components/PageHeader";
import { ProductTable } from "../components/ProductTable";
import { StateMessage } from "../components/StateMessage";
import { ChevronLeftIcon, PencilIcon, TrashIcon } from "../components/icons";
import {
  ApiError,
  api,
  isAbortError,
  toApiError,
} from "../services/api";
import type { Product, ProductListDetail } from "../types/api";
import { formatDate, formatDateTime } from "../utils/datetime";
import { formatInteger } from "../utils/money";
import styles from "./ListDetailPage.module.css";

type DetailState =
  | { status: "loading" }
  | { status: "ready"; detail: ProductListDetail }
  | { status: "error"; error: ApiError };

interface EditValues {
  name: string;
  description: string;
}

interface EditErrors {
  name?: string;
}

type FeedbackState = {
  tone: "success" | "error";
  message: string;
};

export function ListDetailPage() {
  const { listId: listIdParam } = useParams();
  const navigate = useNavigate();
  const parsedId = Number(listIdParam);
  const listId =
    Number.isInteger(parsedId) && parsedId > 0 ? parsedId : null;

  const [state, setState] = useState<DetailState>(() =>
    listId === null
      ? {
          status: "error",
          error: new ApiError(
            "not_found",
            "Lista não encontrada.",
            404,
          ),
        }
      : { status: "loading" },
  );
  const [retryToken, setRetryToken] = useState(0);
  const [editing, setEditing] = useState(false);
  const [editValues, setEditValues] = useState<EditValues>({
    name: "",
    description: "",
  });
  const [editErrors, setEditErrors] = useState<EditErrors>({});
  const [saving, setSaving] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [removingId, setRemovingId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);

  const editNameId = useId();
  const editDescriptionId = useId();
  const confirmTitleId = useId();
  const editNameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (listId === null) {
      return;
    }

    const controller = new AbortController();
    setState({ status: "loading" });
    setEditing(false);
    setEditErrors({});
    setConfirmingDelete(false);
    setFeedback(null);
    setRemovingId(null);

    api
      .getList(listId, { signal: controller.signal })
      .then((detail) => setState({ status: "ready", detail }))
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setState({ status: "error", error: toApiError(cause) });
      });

    return () => controller.abort();
  }, [listId, retryToken]);

  function startEditing(detail: ProductListDetail) {
    setEditValues({
      name: detail.name,
      description: detail.description ?? "",
    });
    setEditErrors({});
    setFeedback(null);
    setConfirmingDelete(false);
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
    setEditErrors({});
  }

  async function handleEditSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state.status !== "ready") {
      return;
    }

    const name = editValues.name.trim();
    if (!name) {
      setEditErrors({ name: "dê um nome para a lista." });
      editNameRef.current?.focus();
      return;
    }

    setEditErrors({});
    setSaving(true);
    setFeedback(null);

    try {
      const updated = await api.updateList(state.detail.id, {
        name,
        description: editValues.description.trim() || null,
      });
      setState((current) =>
        current.status === "ready"
          ? {
              status: "ready",
              detail: {
                ...current.detail,
                ...updated,
              },
            }
          : current,
      );
      setEditing(false);
      setFeedback({ tone: "success", message: "lista atualizada." });
    } catch (cause: unknown) {
      setFeedback({ tone: "error", message: toApiError(cause).message });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(detail: ProductListDetail) {
    setDeleting(true);
    setFeedback(null);

    try {
      await api.deleteList(detail.id);
      navigate("/listas", { replace: true });
    } catch (cause: unknown) {
      setFeedback({ tone: "error", message: toApiError(cause).message });
      setConfirmingDelete(false);
    } finally {
      setDeleting(false);
    }
  }

  async function handleRemoveProduct(product: Product) {
    if (state.status !== "ready") {
      return;
    }

    setRemovingId(product.id);
    setFeedback(null);

    try {
      await api.removeListItem(state.detail.id, product.id);
      setState((current) => {
        if (current.status !== "ready") {
          return current;
        }
        const items = current.detail.items.filter(
          (item) => item.id !== product.id,
        );
        return {
          status: "ready",
          detail: {
            ...current.detail,
            items,
            item_count: items.length,
          },
        };
      });
      setFeedback({
        tone: "success",
        message: `"${product.title}" removido da lista.`,
      });
    } catch (cause: unknown) {
      setFeedback({ tone: "error", message: toApiError(cause).message });
    } finally {
      setRemovingId(null);
    }
  }

  const detail = state.status === "ready" ? state.detail : null;
  const notFound = state.status === "error" && state.error.status === 404;

  return (
    <>
      <Link className={styles.back} to="/listas">
        <ChevronLeftIcon className={styles.backIcon} />
        listas
      </Link>

      <PageHeader
        eyebrow="lista"
        title={detail?.name ?? "lista"}
        description={
          detail
            ? detail.description ??
              "sem descrição. use este espaço para lembrar o objetivo da lista."
            : undefined
        }
        actions={
          <>
            <DemoBadge />
            {detail ? (
              <Link
                className="gz-btn gz-btn--primary"
                to={`/?lista=${detail.id}`}
              >
                adicionar produtos
              </Link>
            ) : null}
          </>
        }
      />

      {state.status === "loading" ? (
        <StateMessage tone="loading" description="carregando a lista…" />
      ) : null}

      {state.status === "error" ? (
        <StateMessage
          tone="error"
          title={notFound ? "lista não encontrada" : "não foi possível carregar a lista"}
          description={
            notFound
              ? "essa lista pode ter sido excluída. volte para listas para ver o que continua disponível."
              : state.error.message
          }
          action={
            <div className={styles.stateActions}>
              <Link className="gz-btn gz-btn--primary" to="/listas">
                voltar para listas
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
              <dt className="gz-label">produtos</dt>
              <dd className={styles.metricValue}>
                {formatInteger(detail.item_count)}
              </dd>
            </div>
            <div className={styles.metric}>
              <dt className="gz-label">criada em</dt>
              <dd className={styles.metricDate}>{formatDate(detail.created_at)}</dd>
            </div>
            <div className={styles.metric}>
              <dt className="gz-label">atualizada em</dt>
              <dd className={styles.metricDate}>
                {formatDateTime(detail.updated_at)}
              </dd>
            </div>
          </dl>

          {editing ? (
            <form className={styles.editForm} onSubmit={handleEditSubmit} noValidate>
              <FormPanel
                title="editar lista"
                description="renomeie ou ajuste a descrição. o nome não pode repetir outra lista."
                footer={
                  <>
                    <button
                      type="submit"
                      className="gz-btn gz-btn--primary"
                      disabled={saving}
                    >
                      {saving ? "salvando…" : "salvar"}
                    </button>
                    <button
                      type="button"
                      className="gz-btn gz-btn--ghost"
                      onClick={cancelEditing}
                      disabled={saving}
                    >
                      cancelar
                    </button>
                  </>
                }
              >
                <div className={styles.editFields}>
                  <div className="gz-field">
                    <label className="gz-label" htmlFor={editNameId}>
                      nome
                    </label>
                    <input
                      ref={editNameRef}
                      id={editNameId}
                      className="gz-input"
                      type="text"
                      value={editValues.name}
                      onChange={(event: ChangeEvent<HTMLInputElement>) =>
                        setEditValues((current) => ({
                          ...current,
                          name: event.target.value,
                        }))
                      }
                      maxLength={120}
                      aria-invalid={Boolean(editErrors.name)}
                      aria-describedby={
                        editErrors.name ? `${editNameId}-error` : undefined
                      }
                    />
                    {editErrors.name ? (
                      <p className="gz-field-error" id={`${editNameId}-error`}>
                        {editErrors.name}
                      </p>
                    ) : null}
                  </div>

                  <div className="gz-field">
                    <label className="gz-label" htmlFor={editDescriptionId}>
                      descrição
                    </label>
                    <textarea
                      id={editDescriptionId}
                      className={`gz-input ${styles.textarea}`}
                      value={editValues.description}
                      onChange={(event: ChangeEvent<HTMLTextAreaElement>) =>
                        setEditValues((current) => ({
                          ...current,
                          description: event.target.value,
                        }))
                      }
                      maxLength={500}
                      rows={2}
                    />
                  </div>
                </div>
              </FormPanel>
            </form>
          ) : (
            <div className={styles.toolbar}>
              <div className={styles.toolbarActions}>
                <button
                  type="button"
                  className="gz-btn gz-btn--outline gz-btn--small"
                  onClick={() => startEditing(detail)}
                >
                  <PencilIcon className={styles.actionIcon} />
                  editar
                </button>
                <button
                  type="button"
                  className="gz-btn gz-btn--ghost gz-btn--small"
                  onClick={() => {
                    setFeedback(null);
                    setConfirmingDelete(true);
                  }}
                >
                  <TrashIcon className={styles.actionIcon} />
                  excluir lista
                </button>
              </div>
              <Link
                className="gz-btn gz-btn--ghost gz-btn--small"
                to={`/?lista=${detail.id}`}
              >
                adicionar da busca
              </Link>
            </div>
          )}

          {confirmingDelete ? (
            <section
              className={styles.confirm}
              aria-labelledby={confirmTitleId}
            >
              <div>
                <h2 className={styles.confirmTitle} id={confirmTitleId}>
                  excluir esta lista?
                </h2>
                <p className={styles.confirmText}>
                  a lista "{detail.name}" será apagada. os produtos continuam no
                  catálogo e podem ser reunidos de novo depois.
                </p>
              </div>
              <div className={styles.confirmActions}>
                <button
                  type="button"
                  className="gz-btn gz-btn--primary gz-btn--small"
                  onClick={() => handleDelete(detail)}
                  disabled={deleting}
                >
                  {deleting ? "excluindo…" : "excluir definitivamente"}
                </button>
                <button
                  type="button"
                  className="gz-btn gz-btn--ghost gz-btn--small"
                  onClick={() => setConfirmingDelete(false)}
                  disabled={deleting}
                >
                  cancelar
                </button>
              </div>
            </section>
          ) : null}

          {feedback ? (
            <div className={styles.feedback}>
              <Feedback tone={feedback.tone}>{feedback.message}</Feedback>
            </div>
          ) : null}

          <section className={styles.products} aria-label="produtos da lista">
            {detail.items.length === 0 ? (
              <EmptyState
                title="lista vazia"
                description="adicione produtos da busca para começar. eles entram na ordem em que forem escolhidos."
                action={
                  <Link
                    className="gz-btn gz-btn--primary"
                    to={`/?lista=${detail.id}`}
                  >
                    adicionar produtos
                  </Link>
                }
              />
            ) : (
              <>
                <div className={styles.productsHead}>
                  <span className="gz-label">produtos na lista</span>
                  <span className={styles.productsCount}>
                    {detail.items.length}{" "}
                    {detail.items.length === 1 ? "produto" : "produtos"}
                  </span>
                </div>
                <ProductTable
                  products={detail.items}
                  caption={`produtos da lista ${detail.name}`}
                  actionsLabel="remover da lista"
                  actions={(product) => (
                    <button
                      type="button"
                      className="gz-icon-btn gz-icon-btn--danger"
                      aria-label={`remover "${product.title}" da lista`}
                      onClick={() => handleRemoveProduct(product)}
                      disabled={removingId === product.id}
                    >
                      <TrashIcon />
                    </button>
                  )}
                />
              </>
            )}
          </section>
        </>
      ) : null}
    </>
  );
}
