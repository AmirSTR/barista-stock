import { CatalogResponse } from '../types/catalog';
import { OrderCreateRequest, OrderCreateResultResponse } from '../types/order';
import { MOCK_CATALOG_DATA } from './mockData';

const viteEnv = (import.meta as { env?: Record<string, string> }).env;
const API_BASE = (viteEnv?.VITE_API_URL ? String(viteEnv.VITE_API_URL).replace(/\/+$/, '') : '') + '/api';

export class ApiService {
  private static localCatalogState: CatalogResponse = JSON.parse(
    JSON.stringify(MOCK_CATALOG_DATA)
  );

  /**
   * Fetch catalog of products grouped by 8 categories.
   */
  public static async getCatalog(): Promise<CatalogResponse> {
    try {
      const response = await fetch(`${API_BASE}/catalog`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: CatalogResponse = await response.json();
      // Cache latest state
      this.localCatalogState = JSON.parse(JSON.stringify(data));
      return data;
    } catch (err) {
      console.warn('⚠️ Could not connect to live backend API, using client mock state:', err);
      return JSON.parse(JSON.stringify(this.localCatalogState));
    }
  }

  /**
   * Create an order for a coffee bar.
   * Atomic row-locking on backend.
   */
  public static async createOrder(
    orderPayload: OrderCreateRequest
  ): Promise<OrderCreateResultResponse> {
    try {
      const response = await fetch(`${API_BASE}/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderPayload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error ${response.status}`);
      }

      const data: OrderCreateResultResponse = await response.json();
      return data;
    } catch (err) {
      console.warn('⚠️ Order API request failed or backend offline. Running mock order processor:', err);
      return this.simulateOrderCreation(orderPayload);
    }
  }

  /**
   * Realistic order simulation when backend is offline for instant dev testing.
   */
  private static simulateOrderCreation(
    payload: OrderCreateRequest
  ): OrderCreateResultResponse {
    const orderId = Math.floor(1000 + Math.random() * 9000);
    const confirmedItems = [];
    const partialItems = [];
    const outOfStockItems = [];

    // Find products in local state
    const allProducts = this.localCatalogState.categories.flatMap((c) => c.items);

    for (const reqItem of payload.items) {
      const product = allProducts.find((p) => p.id === reqItem.product_id);
      if (!product) continue;

      const avail = product.available_qty;

      if (avail >= reqItem.quantity) {
        // Full reserve
        product.available_qty -= reqItem.quantity;
        if (product.available_qty <= 0) product.is_stop = true;

        confirmedItems.push({
          id: Math.floor(Math.random() * 100000),
          product_id: product.id,
          name: product.name,
          sku: product.sku,
          unit: product.unit,
          requested_qty: reqItem.quantity,
          confirmed_qty: reqItem.quantity,
        });
      } else if (avail > 0 && avail < reqItem.quantity) {
        // Partial reserve
        const confirmedQty = avail;
        product.available_qty = 0;
        product.is_stop = true;

        confirmedItems.push({
          id: Math.floor(Math.random() * 100000),
          product_id: product.id,
          name: product.name,
          sku: product.sku,
          unit: product.unit,
          requested_qty: reqItem.quantity,
          confirmed_qty: confirmedQty,
        });

        partialItems.push({
          product_id: product.id,
          name: product.name,
          sku: product.sku,
          requested_qty: reqItem.quantity,
          confirmed_qty: confirmedQty,
          available_before: avail,
          message: `На складе осталось только ${confirmedQty} ${product.unit} (запрошено ${reqItem.quantity} ${product.unit})`,
        });
      } else {
        // Out of stock
        outOfStockItems.push({
          product_id: product.id,
          name: product.name,
          sku: product.sku,
          requested_qty: reqItem.quantity,
          available_before: 0,
          message: `Товар «${product.name}» ушел в стоп и недоступен к заказу`,
        });
      }
    }

    return {
      id: orderId,
      order_id: orderId,
      bar_id: payload.bar_id,
      status: 'pending',
      created_at: new Date().toISOString(),
      items: confirmedItems,
      partial_items: partialItems,
      out_of_stock_items: outOfStockItems,
    };
  }

  /**
   * Helper to trigger mock stock collision for demonstration.
   */
  public static triggerStockCollision(productId: number, newQty: number): void {
    const allProducts = this.localCatalogState.categories.flatMap((c) => c.items);
    const product = allProducts.find((p) => p.id === productId);
    if (product) {
      product.available_qty = newQty;
      product.is_stop = newQty <= 0;
    }
  }
}
