import React from 'react';
import {
  AlertTriangle,
  Ban,
  TrendingDown,
  CheckCircle2,
  ArrowRight,
  RotateCcw,
} from 'lucide-react';
import { useCart } from '../context/CartContext';
import { telegram } from '../services/telegram';

export const StockAlertModal: React.FC = () => {
  const {
    stockAlert,
    setStockAlert,
    acceptStockChangesAndProceed,
  } = useCart();

  if (!stockAlert) return null;

  const { partial_items, out_of_stock_items, orderResult } = stockAlert;

  const handleAccept = () => {
    telegram.hapticNotification('success');
    acceptStockChangesAndProceed();
  };

  const handleBackToCart = () => {
    telegram.hapticImpact('light');
    setStockAlert(null);
  };

  const confirmedCount = orderResult.items.length;
  const partialCount = partial_items.length;
  const outCount = out_of_stock_items.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="w-full max-w-md bg-slate-900 border border-amber-500/40 rounded-3xl shadow-2xl overflow-hidden animate-slide-up flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-5 bg-gradient-to-b from-amber-500/15 to-transparent border-b border-slate-800 text-center shrink-0">
          <div className="w-13 h-13 mx-auto mb-3 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <AlertTriangle className="w-7 h-7" />
          </div>
          <h3 className="text-base font-extrabold text-white">
            Изменение остатков на складе
          </h3>
          <p className="text-xs text-slate-300 mt-1 max-w-xs mx-auto">
            Во время формирования заказа складские остатки изменились из-за параллельных отгрузок в сети:
          </p>
        </div>

        {/* Changes Breakdown List */}
        <div className="p-5 overflow-y-auto space-y-3.5 no-scrollbar flex-1">
          {/* 1. Out of stock items */}
          {outCount > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-rose-400">
                <Ban className="w-4 h-4" />
                <span>Ушли в стоп ({outCount})</span>
              </div>
              <div className="space-y-2">
                {out_of_stock_items.map((item) => (
                  <div
                    key={item.product_id}
                    className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 flex items-start justify-between gap-2"
                  >
                    <div>
                      <div className="text-[10px] font-mono text-rose-300/80">
                        {item.sku}
                      </div>
                      <div className="text-xs font-bold text-slate-100 line-clamp-1">
                        {item.name}
                      </div>
                      <div className="text-[11px] text-rose-300/90 mt-0.5">
                        {item.message || 'Товар закончился и исключен из заказа'}
                      </div>
                    </div>
                    <span className="shrink-0 text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      0 шт
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 2. Partial items */}
          {partialCount > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400">
                <TrendingDown className="w-4 h-4" />
                <span>Количество скорректировано ({partialCount})</span>
              </div>
              <div className="space-y-2">
                {partial_items.map((item) => (
                  <div
                    key={item.product_id}
                    className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 flex items-start justify-between gap-2"
                  >
                    <div>
                      <div className="text-[10px] font-mono text-amber-300/80">
                        {item.sku}
                      </div>
                      <div className="text-xs font-bold text-slate-100 line-clamp-1">
                        {item.name}
                      </div>
                      <div className="text-[11px] text-amber-300/90 mt-0.5">
                        Было {item.requested_qty} → Забронировано: <b className="text-amber-200">{item.confirmed_qty}</b>
                      </div>
                    </div>
                    <span className="shrink-0 text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {item.confirmed_qty} шт
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Fully confirmed items preview summary */}
          {confirmedCount > 0 && (
            <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-between text-xs text-slate-300">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Подтверждено позиций:</span>
              </div>
              <span className="font-bold text-emerald-400">
                {confirmedCount} поз.
              </span>
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 space-y-2 shrink-0">
          <button
            onClick={handleAccept}
            className="w-full py-3.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 active:scale-[0.98] text-white font-bold text-sm shadow-xl shadow-brand-600/30 flex items-center justify-center gap-2 transition-all"
          >
            <span>Принять изменения и продолжить</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={handleBackToCart}
            className="w-full py-2.5 px-4 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white font-semibold text-xs border border-slate-700/60 flex items-center justify-center gap-1.5 transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Вернуться в корзину для замены</span>
          </button>
        </div>
      </div>
    </div>
  );
};
