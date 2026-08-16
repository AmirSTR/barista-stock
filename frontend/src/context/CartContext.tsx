import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Product, CoffeeBar } from '../types/catalog';
import {
  CartItem,
  OrderCreateResultResponse,
  PartialItemWarning,
  OutOfStockItemWarning,
} from '../types/order';
import { INITIAL_BARS } from '../services/mockData';
import { ApiService } from '../services/api';
import { telegram } from '../services/telegram';

interface StockAlertPayload {
  partial_items: PartialItemWarning[];
  out_of_stock_items: OutOfStockItemWarning[];
  orderResult: OrderCreateResultResponse;
}

interface CartContextType {
  cart: Record<number, CartItem>;
  cartItemsList: CartItem[];
  totalPositionsCount: number;
  totalQuantity: number;
  isCartOpen: boolean;
  setIsCartOpen: (open: boolean) => void;
  selectedBar: CoffeeBar;
  setSelectedBar: (bar: CoffeeBar) => void;
  isBarSelectorOpen: boolean;
  setIsBarSelectorOpen: (open: boolean) => void;
  isSubmitting: boolean;
  lastConfirmedOrder: OrderCreateResultResponse | null;
  setLastConfirmedOrder: (order: OrderCreateResultResponse | null) => void;
  stockAlert: StockAlertPayload | null;
  setStockAlert: (alert: StockAlertPayload | null) => void;
  
  // Actions
  addItem: (product: Product, qty?: number) => void;
  decrementItem: (productId: number) => void;
  updateQuantity: (productId: number, qty: number, maxQty?: number) => void;
  removeItem: (productId: number) => void;
  clearCart: () => void;
  getItemQuantity: (productId: number) => number;
  submitOrder: () => Promise<boolean>;
  acceptStockChangesAndProceed: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cart, setCart] = useState<Record<number, CartItem>>({});
  const [isCartOpen, setIsCartOpen] = useState<boolean>(false);
  const [isBarSelectorOpen, setIsBarSelectorOpen] = useState<boolean>(false);
  const [selectedBar, setSelectedBar] = useState<CoffeeBar>(INITIAL_BARS[0]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [lastConfirmedOrder, setLastConfirmedOrder] = useState<OrderCreateResultResponse | null>(null);
  const [stockAlert, setStockAlert] = useState<StockAlertPayload | null>(null);

  // Sync Telegram user start_param if available to set the bar
  useEffect(() => {
    const startParam = telegram.getStartParam();
    if (startParam && startParam.startsWith('bar_')) {
      const barId = parseInt(startParam.replace('bar_', ''), 10);
      const found = INITIAL_BARS.find((b) => b.id === barId);
      if (found) {
        setSelectedBar(found);
      }
    }
  }, []);

  const cartItemsList = Object.values(cart);
  const totalPositionsCount = cartItemsList.length;
  const totalQuantity = cartItemsList.reduce((sum, item) => sum + item.quantity, 0);

  const getItemQuantity = useCallback(
    (productId: number): number => {
      return cart[productId]?.quantity || 0;
    },
    [cart]
  );

  const addItem = useCallback((product: Product, qty = 1) => {
    if (product.is_stop || product.available_qty <= 0) {
      telegram.hapticNotification('warning');
      return;
    }

    setCart((prev) => {
      const current = prev[product.id];
      const newQty = (current ? current.quantity : 0) + qty;
      const finalQty = Math.min(newQty, product.available_qty);

      telegram.hapticImpact('light');

      return {
        ...prev,
        [product.id]: {
          product_id: product.id,
          name: product.name,
          sku: product.sku,
          unit: product.unit,
          category: product.category,
          quantity: finalQty,
          available_qty: product.available_qty,
          is_stop: product.is_stop,
        },
      };
    });
  }, []);

  const decrementItem = useCallback((productId: number) => {
    telegram.hapticImpact('light');
    setCart((prev) => {
      const current = prev[productId];
      if (!current) return prev;

      if (current.quantity <= 1) {
        const copy = { ...prev };
        delete copy[productId];
        return copy;
      }

      return {
        ...prev,
        [productId]: {
          ...current,
          quantity: current.quantity - 1,
        },
      };
    });
  }, []);

  const updateQuantity = useCallback(
    (productId: number, qty: number, maxQty?: number) => {
      setCart((prev) => {
        const current = prev[productId];
        if (!current) return prev;

        if (qty <= 0) {
          const copy = { ...prev };
          delete copy[productId];
          return copy;
        }

        const limit = maxQty !== undefined ? maxQty : current.available_qty;
        const validQty = Math.min(qty, limit);

        telegram.hapticImpact('light');

        return {
          ...prev,
          [productId]: {
            ...current,
            quantity: validQty,
          },
        };
      });
    },
    []
  );

  const removeItem = useCallback((productId: number) => {
    telegram.hapticNotification('warning');
    setCart((prev) => {
      const copy = { ...prev };
      delete copy[productId];
      return copy;
    });
  }, []);

  const clearCart = useCallback(() => {
    setCart({});
  }, []);

  // Submit Order logic
  const submitOrder = useCallback(async (): Promise<boolean> => {
    if (cartItemsList.length === 0 || isSubmitting) return false;

    setIsSubmitting(true);
    telegram.setMainButtonLoading(true);

    try {
      const payload = {
        bar_id: selectedBar.id,
        items: cartItemsList.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
      };

      const result = await ApiService.createOrder(payload);

      // Check if stock changes occurred (partial or out_of_stock)
      const hasPartial = result.partial_items && result.partial_items.length > 0;
      const hasOutOfStock =
        result.out_of_stock_items && result.out_of_stock_items.length > 0;

      if (hasPartial || hasOutOfStock) {
        telegram.hapticNotification('warning');
        setStockAlert({
          partial_items: result.partial_items || [],
          out_of_stock_items: result.out_of_stock_items || [],
          orderResult: result,
        });
        setIsSubmitting(false);
        telegram.setMainButtonLoading(false);
        return false;
      }

      // Order completely successful
      telegram.hapticNotification('success');
      setLastConfirmedOrder(result);
      setCart({});
      setIsCartOpen(false);
      setIsSubmitting(false);
      telegram.setMainButtonLoading(false);
      return true;
    } catch (err) {
      console.error('Order submission failed:', err);
      telegram.hapticNotification('error');
      setIsSubmitting(false);
      telegram.setMainButtonLoading(false);
      return false;
    }
  }, [cartItemsList, isSubmitting, selectedBar.id]);

  // Accept stock changes from alert modal and complete the order
  const acceptStockChangesAndProceed = useCallback(() => {
    if (!stockAlert) return;

    const { orderResult } = stockAlert;
    telegram.hapticNotification('success');

    // Update local cart / finish order with confirmed items
    setLastConfirmedOrder(orderResult);
    setCart({});
    setStockAlert(null);
    setIsCartOpen(false);
  }, [stockAlert]);

  return (
    <CartContext.Provider
      value={{
        cart,
        cartItemsList,
        totalPositionsCount,
        totalQuantity,
        isCartOpen,
        setIsCartOpen,
        selectedBar,
        setSelectedBar,
        isBarSelectorOpen,
        setIsBarSelectorOpen,
        isSubmitting,
        lastConfirmedOrder,
        setLastConfirmedOrder,
        stockAlert,
        setStockAlert,
        addItem,
        decrementItem,
        updateQuantity,
        removeItem,
        clearCart,
        getItemQuantity,
        submitOrder,
        acceptStockChangesAndProceed,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = (): CartContextType => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
