import type {
  AddItemsResponse,
  AffiliateLink,
  CategoriesResponse,
  LinkBatchDetail,
  LinkBatchInput,
  LinkBatchListResponse,
  LinkBatchQuery,
  LinkListResponse,
  LinkQuery,
  LinkRegenerateInput,
  ListInput,
  ListUpdateInput,
  ProductListDetail,
  ProductListSummary,
  ProductQuery,
  ProductSearchResponse,
  SystemConfig,
} from "../types/api";

interface ErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
    request_id?: string | null;
  };
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: unknown;
  readonly requestId: string | null;

  constructor(
    code: string,
    message: string,
    status: number,
    details: unknown = null,
    requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
    this.requestId = requestId;
  }
}

export function isAbortError(value: unknown): boolean {
  return value instanceof DOMException && value.name === "AbortError";
}

export function toApiError(value: unknown): ApiError {
  if (value instanceof ApiError) {
    return value;
  }
  return new ApiError(
    "unknown_error",
    "Não foi possível concluir a operação.",
    0,
  );
}

function buildQuery(params: ProductQuery): string {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.category) search.set("category", params.category);
  if (params.price_min_cents !== undefined) {
    search.set("price_min_cents", String(params.price_min_cents));
  }
  if (params.price_max_cents !== undefined) {
    search.set("price_max_cents", String(params.price_max_cents));
  }
  if (params.min_commission_rate_bp !== undefined) {
    search.set("min_commission_rate_bp", String(params.min_commission_rate_bp));
  }
  if (params.sort && params.sort !== "relevance") {
    search.set("sort", params.sort);
  }
  search.set("page", String(params.page ?? 1));
  search.set("page_size", String(params.page_size ?? 20));
  return search.toString();
}

function buildBatchQuery(params: LinkBatchQuery): string {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.source) search.set("source", params.source);
  search.set("page", String(params.page ?? 1));
  search.set("page_size", String(params.page_size ?? 20));
  return search.toString();
}

function buildLinkQuery(params: LinkQuery): string {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.batch_id !== undefined) {
    search.set("batch_id", String(params.batch_id));
  }
  if (params.status) search.set("status", params.status);
  if (params.sub_id_1) search.set("sub_id_1", params.sub_id_1);
  if (params.sub_id_2) search.set("sub_id_2", params.sub_id_2);
  if (params.sub_id_3) search.set("sub_id_3", params.sub_id_3);
  if (params.source) search.set("source", params.source);
  search.set("page", String(params.page ?? 1));
  search.set("page_size", String(params.page_size ?? 20));
  return search.toString();
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`/api${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    });
  } catch (cause) {
    if (isAbortError(cause)) {
      throw cause;
    }
    throw new ApiError(
      "network_error",
      "Não foi possível falar com a API local. Verifique se o backend está rodando.",
      0,
    );
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | ErrorEnvelope
      | null;
    throw new ApiError(
      payload?.error?.code ?? "http_error",
      payload?.error?.message ?? "Não foi possível atender a solicitação.",
      response.status,
      payload?.error?.details ?? null,
      payload?.error?.request_id ?? null,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function jsonRequest(method: string, body?: unknown): RequestInit {
  return {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  };
}

export const api = {
  getConfig(init?: RequestInit): Promise<SystemConfig> {
    return request<SystemConfig>("/config", init);
  },

  searchProducts(
    query: ProductQuery,
    init?: RequestInit,
  ): Promise<ProductSearchResponse> {
    return request<ProductSearchResponse>(
      `/products/search?${buildQuery(query)}`,
      init,
    );
  },

  getCategories(init?: RequestInit): Promise<CategoriesResponse> {
    return request<CategoriesResponse>("/products/categories", init);
  },

  getLists(init?: RequestInit): Promise<ProductListSummary[]> {
    return request<ProductListSummary[]>("/lists", init);
  },

  getList(listId: number, init?: RequestInit): Promise<ProductListDetail> {
    return request<ProductListDetail>(`/lists/${listId}`, init);
  },

  createList(input: ListInput): Promise<ProductListSummary> {
    return request<ProductListSummary>("/lists", jsonRequest("POST", input));
  },

  updateList(
    listId: number,
    input: ListUpdateInput,
  ): Promise<ProductListSummary> {
    return request<ProductListSummary>(
      `/lists/${listId}`,
      jsonRequest("PATCH", input),
    );
  },

  deleteList(listId: number): Promise<void> {
    return request<void>(`/lists/${listId}`, jsonRequest("DELETE"));
  },

  addListItems(
    listId: number,
    productIds: number[],
  ): Promise<AddItemsResponse> {
    return request<AddItemsResponse>(
      `/lists/${listId}/items`,
      jsonRequest("POST", { product_ids: productIds }),
    );
  },

  removeListItem(listId: number, productId: number): Promise<void> {
    return request<void>(
      `/lists/${listId}/items/${productId}`,
      jsonRequest("DELETE"),
    );
  },

  getLinkBatches(
    query: LinkBatchQuery = {},
    init?: RequestInit,
  ): Promise<LinkBatchListResponse> {
    return request<LinkBatchListResponse>(
      `/link-batches?${buildBatchQuery(query)}`,
      init,
    );
  },

  getLinkBatch(batchId: number, init?: RequestInit): Promise<LinkBatchDetail> {
    return request<LinkBatchDetail>(`/link-batches/${batchId}`, init);
  },

  createLinkBatch(input: LinkBatchInput): Promise<LinkBatchDetail> {
    return request<LinkBatchDetail>(
      "/link-batches",
      jsonRequest("POST", input),
    );
  },

  runLinkBatch(batchId: number): Promise<LinkBatchDetail> {
    return request<LinkBatchDetail>(
      `/link-batches/${batchId}/run`,
      jsonRequest("POST"),
    );
  },

  getLinks(
    query: LinkQuery = {},
    init?: RequestInit,
  ): Promise<LinkListResponse> {
    return request<LinkListResponse>(`/links?${buildLinkQuery(query)}`, init);
  },

  regenerateLink(
    linkId: number,
    input: LinkRegenerateInput,
  ): Promise<AffiliateLink> {
    return request<AffiliateLink>(
      `/links/${linkId}/regenerate`,
      jsonRequest("POST", input),
    );
  },
};
