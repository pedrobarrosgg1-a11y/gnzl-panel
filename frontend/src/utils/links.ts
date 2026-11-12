import type {
  BatchItemStatus,
  BatchStatus,
  DataSource,
  LinkBatchSummary,
  LinkStatus,
} from "../types/api";

export const BATCH_STATUS_LABELS: Record<BatchStatus, string> = {
  pending: "pendente",
  running: "em execução",
  completed: "concluído",
  partial: "parcial",
  failed: "com falha",
};

export const BATCH_ITEM_STATUS_LABELS: Record<BatchItemStatus, string> = {
  pending: "pendente",
  success: "gerado",
  failed: "falhou",
  skipped: "ignorado",
};

export const LINK_STATUS_LABELS: Record<LinkStatus, string> = {
  active: "ativo",
  replaced: "substituído",
};

export const BATCH_STATUS_OPTIONS: ReadonlyArray<{
  value: BatchStatus;
  label: string;
}> = (Object.keys(BATCH_STATUS_LABELS) as BatchStatus[]).map((value) => ({
  value,
  label: BATCH_STATUS_LABELS[value],
}));

export const LINK_STATUS_OPTIONS: ReadonlyArray<{
  value: LinkStatus;
  label: string;
}> = [
  { value: "active", label: "ativos" },
  { value: "replaced", label: "substituídos" },
];

export const SOURCE_OPTIONS: ReadonlyArray<{
  value: DataSource;
  label: string;
}> = [
  { value: "demo", label: "demo" },
  { value: "shopee", label: "shopee" },
  { value: "csv", label: "csv" },
];

export function isBatchStatus(value: string | null): value is BatchStatus {
  return value !== null && value in BATCH_STATUS_LABELS;
}

export function isLinkStatus(value: string | null): value is LinkStatus {
  return value !== null && value in LINK_STATUS_LABELS;
}

export function isDataSource(value: string | null): value is DataSource {
  return value !== null && SOURCE_OPTIONS.some((option) => option.value === value);
}

/** Resumo curto do resultado de um lote para a lista. */
export function batchResultLabel(batch: LinkBatchSummary): string {
  if (batch.status === "pending") {
    return "aguardando execução";
  }
  if (batch.status === "running") {
    return "gerando links…";
  }
  return `${batch.successful_items} de ${batch.total_items} links`;
}

export function batchOriginLabel(batch: LinkBatchSummary): string {
  return batch.destination_type === "list"
    ? `lista #${batch.product_list_id ?? "—"}`
    : "produtos avulsos";
}

export function subIdValues(link: {
  sub_id_1: string | null;
  sub_id_2: string | null;
  sub_id_3: string | null;
  sub_id_4: string | null;
  sub_id_5: string | null;
}): (string | null)[] {
  return [
    link.sub_id_1,
    link.sub_id_2,
    link.sub_id_3,
    link.sub_id_4,
    link.sub_id_5,
  ];
}

export function formatSubIds(link: {
  sub_id_1: string | null;
  sub_id_2: string | null;
  sub_id_3: string | null;
  sub_id_4: string | null;
  sub_id_5: string | null;
}): string {
  const values = subIdValues(link).filter((value): value is string => Boolean(value));
  return values.length > 0 ? values.join(" · ") : "—";
}

const SUB_ID_MAX_LENGTH = 64;

/**
 * Mesma forma canônica usada pelo backend antes de gravar Sub IDs e listas:
 * minúsculas, sem acento, letras/números/hífen, sem hífen nas pontas.
 * Retorna null quando nada aproveitável sobra.
 */
export function normalizeSubIdInput(raw: string): string | null {
  const withoutAccents = raw
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .trim()
    .toLowerCase();
  const cleaned = withoutAccents
    .replace(/[\s_]+/g, "-")
    .replace(/[^a-z0-9-]+/g, "")
    .replace(/-{2,}/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, SUB_ID_MAX_LENGTH)
    .replace(/-+$/, "");
  return cleaned || null;
}

/** Compara os cinco slots ignorando posições vazias. */
export function sameSubIds(
  left: (string | null)[],
  right: (string | null)[],
): boolean {
  return left.every((value, index) => (value ?? null) === (right[index] ?? null));
}

export function parsePositiveInt(value: string | null): number | null {
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

/** Lê `?produtos=1,2,3` sem confiar no formato da URL. */
export function parseProductIds(value: string | null): number[] {
  if (!value) {
    return [];
  }
  const ids = value
    .split(",")
    .map((part) => Number(part.trim()))
    .filter((id) => Number.isInteger(id) && id > 0);
  return [...new Set(ids)];
}
