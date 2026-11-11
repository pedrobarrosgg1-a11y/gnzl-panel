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
