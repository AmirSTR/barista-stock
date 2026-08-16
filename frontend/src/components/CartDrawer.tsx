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
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-lg max-h-[90vh] bg-slate-900 border-t border-x border-slate-700/80 rounded-t-3xl shadow-2xl flex flex-col overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-brand-500/20 text-brand-400 flex items-center justify-center">
              <ShoppingBag className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 leading-none">
                Корзина заказа
              </h2>
              <span className="text-xs text-slate-400">
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
                className="p-2 text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-xl transition-all"
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
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 active:scale-95 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Selected Bar Destination Card */}
        <div className="px-5 pt-3 pb-2 bg-slate-950/50 border-b border-slate-800/80 shrink-0">
          <div className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center shrink-0">
                <Store className="w-3.5 h-3.5" />
              </div>
              <div className="min-w-0">
                <div className="text-[10px] uppercase font-bold text-slate-400 leading-tight">
                  Получатель (Бар)
                </div>
                <div className="text-xs font-bold text-slate-200 truncate">
                  {isBarsLoading ? 'Загрузка кофеен...' : selectedBar.name}
                </div>
                {barsError && (
                  <div className="text-[10px] text-rose-400 mt-0.5">{barsError}</div>
                )}
              </div>
            </div>
            <button
              onClick={() => {
                telegram.hapticImpact('light');
                setIsBarSelectorOpen(true);
              }}
              className="text-[11px] font-semibold text-brand-400 hover:text-brand-300 px-2 py-1 rounded-lg bg-brand-500/10 hover:bg-brand-500/20 shrink-0 transition-all"
            >
              Сменить
            </button>
          </div>
        </div>

        {/* Cart Item List */}
        <div className="flex-1 overflow-y-auto px-5 py-3 space-y-2.5 no-scrollbar">
          {cartItemsList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400 mb-3">
                <ShoppingBag className="w-7 h-7" />
              </div>
              <p className="text-sm font-semibold text-slate-300">
                Корзина пуста
              </p>
              <p className="text-xs text-slate-500 mt-1 max-w-xs">
                Добавьте необходимые товары из каталога для отправки заявки на склад.
              </p>
            </div>
          ) : (
            cartItemsList.map((item) => {
              const isLimit = item.quantity >= item.available_qty;
              return (
                <div
                  key={item.product_id}
                  className="flex items-center justify-between gap-3 p-3 rounded-2xl bg-slate-800/80 border border-slate-700/60 hover:border-slate-600/80 transition-all"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-[9px] font-mono text-slate-400 bg-slate-900/60 px-1.5 py-0.5 rounded">
                        {item.sku}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {item.unit}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-slate-100 truncate leading-snug">
                      {item.name}
                    </h4>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      Доступно на складе: <b className="text-slate-300">{item.available_qty} {item.unit}</b>
                    </div>
                  </div>

                  {/* Actions: Stepper & Remove */}
                  <div className="flex items-center gap-2 shrink-0">
                    <div className="flex items-center bg-slate-900 rounded-xl p-1 border border-slate-700/80">
                      <button
                        onClick={() => decrementItem(item.product_id)}
                        className="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 active:scale-90 flex items-center justify-center text-slate-300 transition-all"
                      >
                        <Minus className="w-3.5 h-3.5" />
                      </button>
                      <span className="w-7 text-center text-xs font-bold text-white">
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
                        className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
                          isLimit
                            ? 'bg-slate-800/40 text-slate-600 cursor-not-allowed'
                            : 'bg-brand-600 hover:bg-brand-500 active:scale-90 text-white'
                        }`}
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <button
                      onClick={() => removeItem(item.product_id)}
                      className="p-1.5 text-slate-400 hover:text-rose-400 active:scale-90 transition-all"
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
          <div className="p-4 bg-slate-950 border-t border-slate-800 shrink-0 space-y-3">
            {submissionError && (
              <div className="flex items-start gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{submissionError}</span>
              </div>
            )}

            {/* Total Row */}
            <div className="flex items-center justify-between text-xs text-slate-300">
              <span className="text-slate-400">Итого позиций к заказу:</span>
              <span className="font-bold text-white text-sm">
                {totalPositionsCount} поз. ({totalQuantity} ед.)
              </span>
            </div>

            {/* In-App Checkout Button (Dual-supported for Web and Telegram) */}
            <button
              onClick={() => submitOrder()}
              disabled={isSubmitting || selectedBar.id <= 0}
              className="w-full py-3.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 active:scale-[0.98] disabled:opacity-60 text-white font-bold text-sm shadow-xl shadow-brand-600/30 flex items-center justify-center gap-2 transition-all"
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
