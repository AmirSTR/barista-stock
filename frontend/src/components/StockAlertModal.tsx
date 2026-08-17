import React from 'react';
import {
  AlertTriangle,
  Ban,
  TrendingDown,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';
import { useCart } from '../context/CartContext';
import { telegram } from '../services/telegram';

export const StockAlertModal: React.FC = () => {
  const {
    stockAlert,
    acceptStockChangesAndProceed,
  } = useCart();

  if (!stockAlert) return null;

  const { partial_items, out_of_stock_items, orderResult } = stockAlert;

  const handleAccept = () => {
    telegram.hapticNotification('success');
    acceptStockChangesAndProceed();
  };

  const confirmedCount = orderResult.items.filter((item) => item.confirmed_qty > 0).length;
  const partialCount = partial_items.length;
  const outCount = out_of_stock_items.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-md bg-tg-bg border border-tg-secondaryBg rounded-2xl shadow-xl overflow-hidden animate-slide-up flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-5 bg-tg-secondaryBg border-b border-tg-secondaryBg text-center shrink-0">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-amber-100 flex items-center justify-center text-amber-600">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-tg-text">
            Изменение остатков на складе
          </h3>
          <p className="text-xs text-tg-hint mt-1 max-w-xs mx-auto">
            Заказ уже создан, а доступные позиции забронированы. Склад скорректировал его по фактическим остаткам:
          </p>
        </div>

        {/* Changes Breakdown List */}
        <div className="p-5 overflow-y-auto space-y-4 no-scrollbar flex-1">
          {/* 1. Out of stock items */}
          {outCount > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-red-600">
                <Ban className="w-4 h-4" />
                <span>Ушли в стоп ({outCount})</span>
              </div>
              <div className="space-y-2">
                {out_of_stock_items.map((item) => (
                  <div
                    key={item.product_id}
                    className="p-3 rounded-xl bg-red-50 border border-red-100 flex items-start justify-between gap-2"
                  >
                    <div>
                      <div className="text-[10px] font-mono text-red-500">
                        {item.sku}
                      </div>
                      <div className="text-xs font-bold text-red-700 line-clamp-1">
                        {item.name}
                      </div>
                      <div className="text-[11px] text-red-600 mt-0.5">
                        {item.message || 'Товар закончился и исключен из заказа'}
                      </div>
                    </div>
                    <span className="shrink-0 text-[10px] font-bold px-2 py-0.5 rounded bg-red-100 text-red-600">
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
              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-600">
                <TrendingDown className="w-4 h-4" />
                <span>Количество скорректировано ({partialCount})</span>
              </div>
              <div className="space-y-2">
                {partial_items.map((item) => (
                  <div
                    key={item.product_id}
                    className="p-3 rounded-xl bg-amber-50 border border-amber-100 flex items-start justify-between gap-2"
                  >
                    <div>
                      <div className="text-[10px] font-mono text-amber-600">
                        {item.sku}
                      </div>
                      <div className="text-xs font-bold text-amber-700 line-clamp-1">
                        {item.name}
                      </div>
                      <div className="text-[11px] text-amber-600 mt-0.5">
                        Было {item.requested_qty} → Забронировано: <b className="text-amber-800">{item.confirmed_qty}</b>
                      </div>
                    </div>
                    <span className="shrink-0 text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-600">
                      {item.confirmed_qty} шт
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Fully confirmed items preview summary */}
          {confirmedCount > 0 && (
            <div className="p-3 rounded-xl bg-brand-50 border border-brand-100 flex items-center justify-between text-xs text-brand-700">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-brand-600" />
                <span>Подтверждено позиций:</span>
              </div>
              <span className="font-bold text-brand-600">
                {confirmedCount} поз.
              </span>
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="p-4 bg-tg-bg border-t border-tg-secondaryBg space-y-2 shrink-0">
          <button
            onClick={handleAccept}
            className="w-full py-3.5 px-4 rounded-md bg-brand-500 hover:bg-brand-600 tap-active text-white font-bold text-sm flex items-center justify-center gap-2 transition-colors"
          >
            <span>Понятно, заказ создан</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
