import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Product, CoffeeBar } from '../types/catalog';
import {
  CartItem,
  OrderCreateResultResponse,
  PartialItemWarning,
  OutOfStockItemWarning,
} from '../types/order';
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
  bars: CoffeeBar[];
  isBarsLoading: boolean;
  barsError: string | null;
  isBarSelectorOpen: boolean;
  setIsBarSelectorOpen: (open: boolean) => void;
  isSubmitting: boolean;
  submissionError: string | null;
  lastConfirmedOrder: OrderCreateResultResponse | null;
  setLastConfirmedOrder: (order: OrderCreateResultResponse | null) => void;
  stockAlert: StockAlertPayload | null;
  
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

const UNSELECTED_BAR: CoffeeBar = {
  id: 0,
  name: 'Выберите кофейню',
  is_active: false,
};

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cart, setCart] = useState<Record<number, CartItem>>({});
  const [isCartOpen, setIsCartOpen] = useState<boolean>(false);
  const [isBarSelectorOpen, setIsBarSelectorOpen] = useState<boolean>(false);
  const [bars, setBars] = useState<CoffeeBar[]>([]);
  const [selectedBar, setSelectedBar] = useState<CoffeeBar>(UNSELECTED_BAR);
  const [isBarsLoading, setIsBarsLoading] = useState<boolean>(true);
  const [barsError, setBarsError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [lastConfirmedOrder, setLastConfirmedOrder] = useState<OrderCreateResultResponse | null>(null);
  const [stockAlert, setStockAlert] = useState<StockAlertPayload | null>(null);

  // Load real backend bars and honor both the bot's ?bar_id=N URL and a
  // Telegram start_param. The URL parameter is what our bot currently emits.
  useEffect(() => {
    let active = true;

    const loadBars = async () => {
      setIsBarsLoading(true);
      setBarsError(null);

      try {
        const loadedBars = await ApiService.getBars();
        if (!active) return;

        setBars(loadedBars);
        if (loadedBars.length === 0) {
          setSelectedBar(UNSELECTED_BAR);
          setBarsError('В системе нет активных кофеен');
          return;
        }

        const queryBarId = new URLSearchParams(window.location.search).get('bar_id');
        const startParam = telegram.getStartParam();
        const startBarId = startParam?.startsWith('bar_')
          ? startParam.slice('bar_'.length)
          : null;
        const requestedId = Number.parseInt(queryBarId || startBarId || '', 10);
        const requestedBar = Number.isFinite(requestedId)
          ? loadedBars.find((bar) => bar.id === requestedId)
          : undefined;

        setSelectedBar(requestedBar || loadedBars[0]);
      } catch (err) {
        if (!active) return;
        console.error('Failed to load coffee bars:', err);
        setSelectedBar(UNSELECTED_BAR);
        setBarsError('Не удалось загрузить список кофеен');
      } finally {
        if (active) setIsBarsLoading(false);
      }
    };

    loadBars();
    return () => {
      active = false;
    };
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
    if (selectedBar.id <= 0 || !selectedBar.is_active) {
      setSubmissionError('Сначала выберите активную кофейню');
      setIsBarSelectorOpen(true);
      return false;
    }

    setIsSubmitting(true);
    setSubmissionError(null);
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
      setSubmissionError(
        err instanceof Error
          ? err.message
          : 'Не удалось оформить заказ. Проверьте подключение и повторите попытку.'
      );
      telegram.hapticNotification('error');
      setIsSubmitting(false);
      telegram.setMainButtonLoading(false);
      return false;
    }
  }, [cartItemsList, isSubmitting, selectedBar.id, selectedBar.is_active]);

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
        bars,
        isBarsLoading,
        barsError,
        isBarSelectorOpen,
        setIsBarSelectorOpen,
        isSubmitting,
        submissionError,
        lastConfirmedOrder,
        setLastConfirmedOrder,
        stockAlert,
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
