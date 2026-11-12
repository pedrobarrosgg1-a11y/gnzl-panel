export type SortOption =
  | "relevance"
  | "commission_desc"
  | "sales_desc"
  | "rating_desc"
  | "price_asc"
  | "price_desc";

export interface SystemConfig {
  version: string;
  environment: "dev" | "prod";
  provider: "demo" | "shopee";
  is_demo: boolean;
}

export interface Product {
  id: number;
  item_id: number;
  shop_id: number;
  title: string;
  image_url: string | null;
  product_url: string | null;
  price_cents: number;
  commission_rate_bp: number;
  sales: number | null;
  rating_x100: number | null;
  category: string | null;
  source: string;
}

export interface ProductSearchResponse {
  items: Product[];
  page: number;
  page_size: number;
  has_next: boolean;
  total: number | null;
  source: string;
  is_demo: boolean;
}

export interface CategoriesResponse {
  items: string[];
  source: string;
  is_demo: boolean;
}

export interface ProductListSummary {
  id: number;
  name: string;
  description: string | null;
  item_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProductListDetail extends ProductListSummary {
  items: Product[];
}

export interface ListInput {
  name: string;
  description?: string | null;
}

export interface ListUpdateInput {
  name?: string;
  description?: string | null;
}

export interface AddItemsResponse {
  added: number;
  skipped: number;
  item_count: number;
  items: Product[];
}

export interface ProductQuery {
  q?: string;
  category?: string;
  price_min_cents?: number;
  price_max_cents?: number;
  min_commission_rate_bp?: number;
  sort?: SortOption;
  page?: number;
  page_size?: number;
}

export type DataSource = "demo" | "shopee" | "csv";
export type BatchStatus =
  | "pending"
  | "running"
  | "completed"
  | "partial"
  | "failed";
export type BatchItemStatus = "pending" | "success" | "failed" | "skipped";
export type LinkStatus = "active" | "replaced";

export interface LinkBatchItem {
  id: number;
  product_id: number | null;
  product: Product | null;
  original_url: string;
  status: BatchItemStatus;
  affiliate_link_id: number | null;
  affiliate_url: string | null;
  error_code: string | null;
  error_message: string | null;
  attempts: number;
  processed_at: string | null;
  created_at: string;
}

export interface LinkBatchSummary {
  id: number;
  name: string | null;
  destination_type: "product" | "list";
  product_list_id: number | null;
  observation: string | null;
  sub_id_1: string | null;
  sub_id_2: string | null;
  sub_id_3: string | null;
  sub_id_4: string | null;
  sub_id_5: string | null;
  source: string;
  is_demo: boolean;
  total_items: number;
  successful_items: number;
  failed_items: number;
  status: BatchStatus;
  created_at: string;
  finished_at: string | null;
}

export interface LinkBatchDetail extends LinkBatchSummary {
  items: LinkBatchItem[];
}

export interface LinkBatchListResponse {
  items: LinkBatchSummary[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
}

export interface LinkBatchQuery {
  status?: BatchStatus;
  source?: DataSource;
  page?: number;
  page_size?: number;
}

export interface LinkBatchInput {
  name?: string | null;
  destination_type: "product" | "list";
  product_ids?: number[];
  product_list_id?: number | null;
  observation?: string | null;
  sub_id_1?: string | null;
  sub_id_2?: string | null;
  sub_id_3?: string | null;
  sub_id_4?: string | null;
  sub_id_5?: string | null;
}

export interface AffiliateLink {
  id: number;
  product_id: number | null;
  product: Product | null;
  link_batch_id: number | null;
  original_url: string;
  affiliate_url: string;
  sub_id_1: string | null;
  sub_id_2: string | null;
  sub_id_3: string | null;
  sub_id_4: string | null;
  sub_id_5: string | null;
  observation: string | null;
  status: LinkStatus;
  replaced_by_id: number | null;
  source: string;
  is_demo: boolean;
  created_at: string;
}

export interface LinkListResponse {
  items: AffiliateLink[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
}

export interface LinkQuery {
  q?: string;
  batch_id?: number;
  status?: LinkStatus;
  sub_id_1?: string;
  sub_id_2?: string;
  sub_id_3?: string;
  source?: DataSource;
  page?: number;
  page_size?: number;
}

export interface LinkRegenerateInput {
  sub_id_1?: string | null;
  sub_id_2?: string | null;
  sub_id_3?: string | null;
  sub_id_4?: string | null;
  sub_id_5?: string | null;
  observation?: string | null;
}
