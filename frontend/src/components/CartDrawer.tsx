import React, { useEffect } from 'react';
import {
  X,
  Trash2,
  Plus,
  Minus,
  ShoppingBag,
  Store,
  ArrowRight,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useCart } from '../context/CartContext';
import { telegram } from '../services/telegram';

export const CartDrawer: React.FC = () => {
  const {
    isCartOpen,
    setIsCartOpen,
    cartItemsList,
    totalPositionsCount,
    totalQuantity,
    selectedBar,
    isBarsLoading,
    barsError,
    setIsBarSelectorOpen,
    decrementItem,
    addItem,
    removeItem,
    clearCart,
    submitOrder,
    isSubmitting,
    submissionError,
  } = useCart();

  // Bind Telegram MainButton and BackButton when cart is open
  useEffect(() => {
    if (isCartOpen) {
      telegram.setupBackButton(() => {
        setIsCartOpen(false);
      });

      if (cartItemsList.length > 0) {
        telegram.setupMainButton({
          text: `Оформить заказ (${totalPositionsCount} поз.)`,
          onClick: () => {
            submitOrder();
          },
          isVisible: true,
          isActive: !isSubmitting && selectedBar.id > 0,
        });
      } else {
        telegram.hideMainButton();
      }
    } else {
      telegram.hideBackButton();
      telegram.hideMainButton();
    }

    return () => {
      telegram.clearMainButtonClick();
      telegram.clearBackButtonClick();
    };
  }, [isCartOpen, cartItemsList.length, totalPositionsCount, isSubmitting, selectedBar.id, setIsCartOpen, submitOrder]);

  if (!isCartOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-lg max-h-[90vh] bg-tg-bg border-t border-x border-tg-secondaryBg rounded-t-2xl shadow-[0_-8px_30px_rgba(0,0,0,0.1)] flex flex-col overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-tg-secondaryBg shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-100 text-brand-600 flex items-center justify-center">
              <ShoppingBag className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-tg-text leading-none">
                Корзина заказа
              </h2>
              <span className="text-xs text-tg-hint">
                {totalPositionsCount} поз. • {totalQuantity} ед.
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {cartItemsList.length > 0 && (
              <button
                onClick={() => {
                  telegram.hapticNotification('warning');
                  clearCart();
                }}
                className="p-2 text-xs font-semibold text-red-500 hover:bg-red-50 rounded-md transition-colors"
                title="Очистить корзину"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => {
                telegram.hapticImpact('light');
                setIsCartOpen(false);
              }}
              className="p-2 rounded-md text-tg-hint hover:text-tg-text hover:bg-tg-secondaryBg tap-active transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Selected Bar Destination Card */}
        <div className="px-5 pt-3 pb-2 bg-tg-bg border-b border-tg-secondaryBg shrink-0">
          <div className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-tg-secondaryBg border border-transparent">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 rounded-md bg-brand-100 text-brand-600 flex items-center justify-center shrink-0">
                <Store className="w-3.5 h-3.5" />
              </div>
              <div className="min-w-0">
                <div className="text-[10px] uppercase font-bold text-tg-hint leading-tight">
                  Получатель (Бар)
                </div>
                <div className="text-xs font-bold text-tg-text truncate">
                  {isBarsLoading ? 'Загрузка кофеен...' : selectedBar.name}
                </div>
                {barsError && (
                  <div className="text-[10px] text-red-500 mt-0.5">{barsError}</div>
                )}
              </div>
            </div>
            <button
              onClick={() => {
                telegram.hapticImpact('light');
                setIsBarSelectorOpen(true);
              }}
              className="text-[11px] font-semibold text-brand-600 hover:text-brand-700 px-2 py-1 rounded-md bg-brand-50 hover:bg-brand-100 shrink-0 transition-colors"
            >
              Сменить
            </button>
          </div>
        </div>

        {/* Cart Item List */}
        <div className="flex-1 overflow-y-auto px-5 py-3 space-y-2.5 no-scrollbar">
          {cartItemsList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-14 h-14 rounded-xl bg-tg-secondaryBg flex items-center justify-center text-tg-hint mb-3">
                <ShoppingBag className="w-7 h-7" />
              </div>
              <p className="text-sm font-semibold text-tg-text">
                Корзина пуста
              </p>
              <p className="text-xs text-tg-hint mt-1 max-w-xs">
                Добавьте необходимые товары из каталога для отправки заявки на склад.
              </p>
            </div>
          ) : (
            cartItemsList.map((item) => {
              const isLimit = item.quantity >= item.available_qty;
              return (
                <div
                  key={item.product_id}
                  className="flex items-center justify-between gap-3 p-3 rounded-xl bg-tg-bg border border-tg-secondaryBg hover:border-brand-200 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-[9px] font-mono text-tg-hint bg-tg-secondaryBg px-1.5 py-0.5 rounded-sm">
                        {item.sku}
                      </span>
                      <span className="text-[10px] text-tg-hint">
                        {item.unit}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-tg-text truncate leading-snug">
                      {item.name}
                    </h4>
                    <div className="text-[10px] text-tg-hint mt-0.5">
                      Доступно на складе: <b className="text-brand-600">{item.available_qty} {item.unit}</b>
                    </div>
                  </div>

                  {/* Actions: Stepper & Remove */}
                  <div className="flex items-center gap-2 shrink-0">
                    <div className="flex items-center bg-brand-50 rounded-md p-1 border border-brand-200">
                      <button
                        onClick={() => decrementItem(item.product_id)}
                        className="w-7 h-7 rounded bg-transparent hover:bg-brand-100 tap-active flex items-center justify-center text-brand-600 transition-colors"
                      >
                        <Minus className="w-3.5 h-3.5" />
                      </button>
                      <span className="w-7 text-center text-xs font-bold text-brand-700">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() =>
                          addItem(
                            {
                              id: item.product_id,
                              name: item.name,
                              sku: item.sku,
                              unit: item.unit,
                              category: item.category,
                              available_qty: item.available_qty,
                              is_stop: item.is_stop,
                            },
                            1
                          )
                        }
                        disabled={isLimit}
                        className={`w-7 h-7 rounded flex items-center justify-center transition-colors ${
                          isLimit
                            ? 'text-brand-300 cursor-not-allowed'
                            : 'bg-brand-500 hover:bg-brand-600 tap-active text-white'
                        }`}
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <button
                      onClick={() => removeItem(item.product_id)}
                      className="p-1.5 text-tg-hint hover:text-red-500 tap-active transition-colors"
                      title="Удалить"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Checkout Action */}
        {cartItemsList.length > 0 && (
          <div className="p-4 bg-tg-bg border-t border-tg-secondaryBg shrink-0 space-y-3">
            {submissionError && (
              <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-xs text-red-600">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{submissionError}</span>
              </div>
            )}

            {/* Total Row */}
            <div className="flex items-center justify-between text-xs text-tg-hint">
              <span className="text-tg-hint">Итого позиций к заказу:</span>
              <span className="font-bold text-tg-text text-sm">
                {totalPositionsCount} поз. ({totalQuantity} ед.)
              </span>
            </div>

            {/* In-App Checkout Button (Dual-supported for Web and Telegram) */}
            <button
              onClick={() => submitOrder()}
              disabled={isSubmitting || selectedBar.id <= 0}
              className="w-full py-3.5 px-4 rounded-md bg-brand-500 hover:bg-brand-600 tap-active disabled:opacity-60 text-white font-bold text-sm flex items-center justify-center gap-2 transition-colors"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Отправка заказа на склад...</span>
                </>
              ) : (
                <>
                  <span>Оформить заказ ({totalPositionsCount} поз.)</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
