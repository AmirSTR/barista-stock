export interface Product {
  id: number;
  name: string;
  sku: string;
  category: string;
  unit: string;
  available_qty: number;
  is_stop: boolean;
  price?: number;
  image?: string;
  description?: string;
}

export interface CategoryGroup {
  category: string;
  items_count: number;
  items: Product[];
}

export interface CatalogResponse {
  total_categories: number;
  total_products: number;
  categories: CategoryGroup[];
}

export interface CoffeeBar {
  id: number;
  name: string;
  address?: string;
  telegram_chat_id?: number;
  is_active: boolean;
}
