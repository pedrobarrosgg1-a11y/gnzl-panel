import {
  useEffect,
  useId,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { Link } from "react-router";

import { DemoBadge } from "../components/DemoBadge";
import { EmptyState } from "../components/EmptyState";
import { Feedback } from "../components/Feedback";
import { FormPanel } from "../components/FormPanel";
import { PageHeader } from "../components/PageHeader";
import { StateMessage } from "../components/StateMessage";
import { api, isAbortError, toApiError, type ApiError } from "../services/api";
import type { ProductListSummary } from "../types/api";
import { formatDate } from "../utils/datetime";
import { formatInteger } from "../utils/money";
import styles from "./ListsPage.module.css";

type ListsState =
  | { status: "loading" }
  | { status: "ready"; lists: ProductListSummary[] }
  | { status: "error"; error: ApiError };

interface FormValues {
  name: string;
  description: string;
}

interface FormErrors {
  name?: string;
}

const EMPTY_FORM: FormValues = { name: "", description: "" };

export function ListsPage() {
  const [state, setState] = useState<ListsState>({ status: "loading" });
  const [retryToken, setRetryToken] = useState(0);
  const [form, setForm] = useState<FormValues>(EMPTY_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    tone: "success" | "error";
    message: string;
  } | null>(null);

  const nameId = useId();
  const descriptionId = useId();
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });

    api
      .getLists({ signal: controller.signal })
      .then((lists) => setState({ status: "ready", lists }))
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setState({ status: "error", error: toApiError(cause) });
      });

    return () => controller.abort();
  }, [retryToken]);

  function updateField<K extends keyof FormValues>(
    key: K,
    value: FormValues[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = form.name.trim();
    if (!name) {
      setErrors({ name: "dê um nome para a lista." });
      nameRef.current?.focus();
      return;
    }

    setErrors({});
    setFeedback(null);
    setSubmitting(true);

    try {
      const created = await api.createList({
        name,
        description: form.description.trim() || null,
      });
      setForm(EMPTY_FORM);
      setFeedback({
        tone: "success",
        message: `lista "${created.name}" criada.`,
      });
      setState((current) =>
        current.status === "ready"
          ? { status: "ready", lists: [created, ...current.lists] }
          : { status: "ready", lists: [created] },
      );
    } catch (cause: unknown) {
      setFeedback({ tone: "error", message: toApiError(cause).message });
    } finally {
      setSubmitting(false);
    }
  }

  function focusCreateForm() {
    nameRef.current?.focus();
  }

  return (
    <>
      <PageHeader
        eyebrow="listas"
        title="suas listas"
        description="reúna produtos por campanha, ideia ou momento. a lista é o ponto de partida para gerar links em lote."
        actions={<DemoBadge />}
      />

      <form className={styles.form} onSubmit={handleSubmit} noValidate>
        <FormPanel
          title="criar lista"
          description="use um nome curto e fácil de reconhecer depois. descrição é opcional."
          footer={
            <button
              type="submit"
              className="gz-btn gz-btn--primary"
              disabled={submitting}
            >
              {submitting ? "criando…" : "criar lista"}
            </button>
          }
        >
          <div className={styles.fields}>
            <div className="gz-field">
              <label className="gz-label" htmlFor={nameId}>
                nome
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
                maxLength={120}
                placeholder="Black Friday, stories de verão…"
                aria-invalid={Boolean(errors.name)}
                aria-describedby={errors.name ? `${nameId}-error` : undefined}
              />
              {errors.name ? (
                <p className="gz-field-error" id={`${nameId}-error`}>
                  {errors.name}
                </p>
              ) : null}
            </div>

            <div className="gz-field">
              <label className="gz-label" htmlFor={descriptionId}>
                descrição
              </label>
              <textarea
                id={descriptionId}
                className={`gz-input ${styles.textarea}`}
                value={form.description}
                onChange={(event: ChangeEvent<HTMLTextAreaElement>) =>
                  updateField("description", event.target.value)
                }
                maxLength={500}
                rows={2}
                placeholder="o que entra nesta lista?"
              />
            </div>
          </div>
        </FormPanel>
      </form>

      {feedback ? (
        <div className={styles.feedback}>
          <Feedback tone={feedback.tone}>{feedback.message}</Feedback>
        </div>
      ) : null}

      <section className={styles.section} aria-label="listas criadas">
        {state.status === "loading" ? (
          <StateMessage
            tone="loading"
            description="carregando suas listas…"
          />
        ) : null}

        {state.status === "error" ? (
          <StateMessage
            tone="error"
            title="não foi possível carregar as listas"
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
          state.lists.length === 0 ? (
            <EmptyState
              title="nenhuma lista ainda"
              description="crie uma lista para reunir produtos por campanha ou ideia. depois adicione produtos direto da busca."
              action={
                <button
                  type="button"
                  className="gz-btn gz-btn--outline"
                  onClick={focusCreateForm}
                >
                  criar primeira lista
                </button>
              }
            />
          ) : (
            <>
              <div className={styles.meta}>
                <span className="gz-label">listas criadas</span>
                <span className={styles.count}>
                  {state.lists.length}{" "}
                  {state.lists.length === 1 ? "lista" : "listas"}
                </span>
              </div>

              <div className={styles.tableWrap}>
                <table className="gz-table">
                  <caption className="gz-visually-hidden">
                    listas criadas com quantidade de produtos e data de
                    atualização
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">lista</th>
                      <th scope="col">descrição</th>
                      <th scope="col" className="gz-num">
                        produtos
                      </th>
                      <th scope="col" className="gz-num">
                        atualizada em
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {state.lists.map((list) => (
                      <tr key={list.id}>
                        <td>
                          <Link
                            className={styles.listLink}
                            to={`/listas/${list.id}`}
                          >
                            {list.name}
                          </Link>
                        </td>
                        <td className={styles.description}>
                          {list.description ?? "—"}
                        </td>
                        <td className="gz-num">{formatInteger(list.item_count)}</td>
                        <td className="gz-num">{formatDate(list.updated_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )
        ) : null}
      </section>
    </>
  );
}
