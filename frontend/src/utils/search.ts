import type { ProductQuery, SortOption } from "../types/api";
import { parseBRLToCents, parsePercentToBp } from "./money";

export const SORT_OPTIONS: ReadonlyArray<{ value: SortOption; label: string }> = [
  { value: "relevance", label: "relevância" },
  { value: "commission_desc", label: "maior comissão" },
  { value: "sales_desc", label: "mais vendidos" },
  { value: "rating_desc", label: "melhor avaliação" },
  { value: "price_asc", label: "menor preço" },
  { value: "price_desc", label: "maior preço" },
];

const SORT_VALUES = new Set<string>(SORT_OPTIONS.map((option) => option.value));

export interface SearchFormValues {
  q: string;
  category: string;
  sort: SortOption;
  priceMin: string;
  priceMax: string;
  commissionMin: string;
}

export interface SearchFormErrors {
  priceMin?: string;
  priceMax?: string;
  commissionMin?: string;
  range?: string;
}

export const EMPTY_SEARCH_FORM: SearchFormValues = {
  q: "",
  category: "",
  sort: "relevance",
  priceMin: "",
  priceMax: "",
  commissionMin: "",
};

function isSort(value: string | null): value is SortOption {
  return value !== null && SORT_VALUES.has(value);
}

function centsToInput(value: string | null): string {
  if (value === null || value === "") {
    return "";
  }
  const cents = Number(value);
  if (!Number.isFinite(cents)) {
    return "";
  }
  return (cents / 100).toFixed(2).replace(".", ",");
}

function basisPointsToInput(value: string | null): string {
  if (value === null || value === "") {
    return "";
  }
  const basisPoints = Number(value);
  if (!Number.isFinite(basisPoints)) {
    return "";
  }
  return (basisPoints / 100).toFixed(2).replace(".", ",");
}

export function formValuesFromParams(params: URLSearchParams): SearchFormValues {
  const sort = params.get("sort");
  return {
    q: params.get("q") ?? "",
    category: params.get("category") ?? "",
    sort: isSort(sort) ? sort : "relevance",
    priceMin: centsToInput(params.get("price_min_cents")),
    priceMax: centsToInput(params.get("price_max_cents")),
    commissionMin: basisPointsToInput(params.get("min_commission_rate_bp")),
  };
}

export interface BuiltSearch {
  query: ProductQuery | null;
  errors: SearchFormErrors;
}

export function buildSearch(values: SearchFormValues): BuiltSearch {
  const errors: SearchFormErrors = {};

  const priceMin = values.priceMin.trim()
    ? parseBRLToCents(values.priceMin)
    : null;
  if (values.priceMin.trim() && priceMin === null) {
    errors.priceMin = "informe um valor em reais, por exemplo 19,90.";
  }

  const priceMax = values.priceMax.trim()
    ? parseBRLToCents(values.priceMax)
    : null;
  if (values.priceMax.trim() && priceMax === null) {
    errors.priceMax = "informe um valor em reais, por exemplo 99,90.";
  }

  const commissionMin = values.commissionMin.trim()
    ? parsePercentToBp(values.commissionMin)
    : null;
  if (values.commissionMin.trim() && commissionMin === null) {
    errors.commissionMin = "informe um percentual entre 0 e 100.";
  }

  if (
    priceMin !== null &&
    priceMax !== null &&
    priceMin > priceMax
  ) {
    errors.range = "o preço mínimo não pode ser maior que o máximo.";
  }

  if (Object.keys(errors).length > 0) {
    return { query: null, errors };
  }

  const query: ProductQuery = {
    sort: values.sort,
  };
  if (values.q.trim()) query.q = values.q.trim();
  if (values.category) query.category = values.category;
  if (priceMin !== null) query.price_min_cents = priceMin;
  if (priceMax !== null) query.price_max_cents = priceMax;
  if (commissionMin !== null) query.min_commission_rate_bp = commissionMin;

  return { query, errors: {} };
}

export function paramsFromValues(values: SearchFormValues): URLSearchParams {
  const { query } = buildSearch(values);
  const params = new URLSearchParams();
  if (query?.q) params.set("q", query.q);
  if (query?.category) params.set("category", query.category);
  if (query?.sort && query.sort !== "relevance") {
    params.set("sort", query.sort);
  }
  if (query?.price_min_cents !== undefined) {
    params.set("price_min_cents", String(query.price_min_cents));
  }
  if (query?.price_max_cents !== undefined) {
    params.set("price_max_cents", String(query.price_max_cents));
  }
  if (query?.min_commission_rate_bp !== undefined) {
    params.set("min_commission_rate_bp", String(query.min_commission_rate_bp));
  }
  params.set("page", "1");
  return params;
}

export function queryFromParams(params: URLSearchParams): ProductQuery {
  const query: ProductQuery = {
    page: Math.max(1, Number(params.get("page")) || 1),
    page_size: 20,
  };
  const q = params.get("q");
  const category = params.get("category");
  const sort = params.get("sort");
  const priceMin = Number(params.get("price_min_cents"));
  const priceMax = Number(params.get("price_max_cents"));
  const commissionMin = Number(params.get("min_commission_rate_bp"));

  if (q) query.q = q;
  if (category) query.category = category;
  if (isSort(sort)) query.sort = sort;
  if (params.get("price_min_cents") && Number.isFinite(priceMin)) {
    query.price_min_cents = priceMin;
  }
  if (params.get("price_max_cents") && Number.isFinite(priceMax)) {
    query.price_max_cents = priceMax;
  }
  if (params.get("min_commission_rate_bp") && Number.isFinite(commissionMin)) {
    query.min_commission_rate_bp = commissionMin;
  }

  return query;
}

export function hasFilterErrors(errors: SearchFormErrors): boolean {
  return Object.keys(errors).length > 0;
}
