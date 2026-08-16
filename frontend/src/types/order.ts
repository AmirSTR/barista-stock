export interface OrderItemInput {
  product_id: number;
  quantity: number;
}

export interface OrderCreateRequest {
  bar_id: number;
  items: OrderItemInput[];
}

export interface OrderConfirmedItem {
  id: number;
  product_id: number;
  name: string;
  sku: string;
  unit: string;
  requested_qty: number;
  confirmed_qty: number;
}

export interface PartialItemWarning {
  product_id: number;
  name: string;
  sku: string;
  requested_qty: number;
  confirmed_qty: number;
  available_before: number;
  message: string;
}

export interface OutOfStockItemWarning {
  product_id: number;
  name: string;
  sku: string;
  requested_qty: number;
  available_before: number;
  message: string;
}

export interface OrderCreateResultResponse {
  id: number;
  order_id: number;
  bar_id: number;
  status: 'pending' | 'packing' | 'shipped' | 'cancelled';
  created_at: string;
  items: OrderConfirmedItem[];
  partial_items: PartialItemWarning[];
  out_of_stock_items: OutOfStockItemWarning[];
}

export interface CartItem {
  product_id: number;
  name: string;
  sku: string;
  unit: string;
  category: string;
  quantity: number;
  available_qty: number;
  is_stop: boolean;
}
