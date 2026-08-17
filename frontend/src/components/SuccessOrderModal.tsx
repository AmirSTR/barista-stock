import React, { useEffect } from 'react';
import {
  CheckCircle,
  PackageCheck,
  Calendar,
  Store,
  Clock,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { useCart } from '../context/CartContext';
import { telegram } from '../services/telegram';

export const SuccessOrderModal: React.FC = () => {
  const {
    lastConfirmedOrder,
    setLastConfirmedOrder,
    selectedBar,
  } = useCart();

  useEffect(() => {
    if (lastConfirmedOrder) {
      telegram.hapticNotification('success');
    }
  }, [lastConfirmedOrder]);

  if (!lastConfirmedOrder) return null;

  const handleClose = () => {
    telegram.hapticImpact('light');
    setLastConfirmedOrder(null);
  };

  const totalConfirmedUnits = lastConfirmedOrder.items.reduce(
    (sum, it) => sum + it.confirmed_qty,
    0
  );

  const formattedDate = new Date(lastConfirmedOrder.created_at).toLocaleString(
    'ru-RU',
    {
      day: '2-digit',
      month: 'long',
      hour: '2-digit',
      minute: '2-digit',
    }
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-md bg-tg-bg border border-tg-secondaryBg rounded-2xl shadow-xl overflow-hidden animate-slide-up flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Celebration Header */}
        <div className="p-6 bg-tg-secondaryBg border-b border-tg-secondaryBg text-center shrink-0">
          <div className="relative inline-block mb-3">
            <div className="w-16 h-16 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 shadow-sm">
              <CheckCircle className="w-8 h-8" />
            </div>
            <Sparkles className="w-5 h-5 text-amber-500 absolute -top-1 -right-1" />
          </div>

          <span className="inline-block px-3 py-1 rounded-sm text-[11px] font-bold uppercase tracking-wider bg-brand-50 text-brand-700 border border-brand-100 mb-1.5">
            Заказ успешно оформлен
          </span>

          <h2 className="text-2xl font-bold text-tg-text">
            Заказ #{lastConfirmedOrder.id || lastConfirmedOrder.order_id}
          </h2>

          <p className="text-xs text-tg-hint mt-1">
            Заявка передана на центральный склад и ожидает сборки
          </p>
        </div>

        {/* Order Details Body */}
        <div className="p-5 overflow-y-auto space-y-4 no-scrollbar flex-1">
          {/* Metadata Cards */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-3 rounded-xl bg-tg-secondaryBg border border-transparent">
              <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-tg-hint mb-1">
                <Store className="w-3.5 h-3.5 text-brand-500" />
                <span>Точка (Бар)</span>
              </div>
              <div className="text-xs font-bold text-tg-text truncate">
                {selectedBar.name}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-tg-secondaryBg border border-transparent">
              <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-tg-hint mb-1">
                <Clock className="w-3.5 h-3.5 text-brand-500" />
                <span>Статус</span>
              </div>
              <div className="text-xs font-bold text-brand-600 capitalize">
                В обработке
              </div>
            </div>
          </div>

          {/* Confirmed Items List */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-tg-text px-1">
              <div className="flex items-center gap-1.5">
                <PackageCheck className="w-4 h-4 text-brand-500" />
                <span>Забронированные позиции ({lastConfirmedOrder.items.length})</span>
              </div>
              <span className="text-tg-hint font-medium text-[11px]">
                Всего: {totalConfirmedUnits} ед.
              </span>
            </div>

            <div className="space-y-1.5 max-h-56 overflow-y-auto no-scrollbar">
              {lastConfirmedOrder.items.map((item) => (
                <div
                  key={item.id || item.product_id}
                  className="p-2.5 rounded-xl bg-tg-bg border border-tg-secondaryBg flex items-center justify-between gap-2"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px] font-mono text-tg-hint bg-tg-secondaryBg px-1.5 py-0.5 rounded-sm">
                        {item.sku}
                      </span>
                      <span className="text-[10px] text-tg-hint">
                        {item.unit}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-tg-text truncate mt-0.5">
                      {item.name}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs font-bold text-brand-700 bg-brand-50 px-2 py-1 rounded-md">
                      {item.confirmed_qty} {item.unit}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-center gap-1.5 text-[11px] text-tg-hint">
            <Calendar className="w-3.5 h-3.5" />
            <span>Оформлено: {formattedDate}</span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-tg-bg border-t border-tg-secondaryBg shrink-0">
          <button
            onClick={handleClose}
            className="w-full py-3.5 px-4 rounded-md bg-brand-500 hover:bg-brand-600 tap-active text-white font-bold text-sm flex items-center justify-center gap-2 transition-colors"
          >
            <span>Сделать новый заказ</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
