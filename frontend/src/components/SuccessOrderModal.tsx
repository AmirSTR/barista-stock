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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="w-full max-w-md bg-slate-900 border border-slate-700/80 rounded-3xl shadow-2xl overflow-hidden animate-slide-up flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Celebration Header */}
        <div className="p-6 bg-gradient-to-b from-emerald-500/20 via-emerald-500/5 to-transparent border-b border-slate-800 text-center shrink-0">
          <div className="relative inline-block mb-3">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-xl shadow-emerald-500/20">
              <CheckCircle className="w-9 h-9 animate-bounce-subtle" />
            </div>
            <Sparkles className="w-5 h-5 text-amber-400 absolute -top-1 -right-1 animate-pulse" />
          </div>

          <span className="inline-block px-3 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 mb-1.5">
            Заказ успешно оформлен
          </span>

          <h2 className="text-2xl font-extrabold text-white">
            Заказ #{lastConfirmedOrder.id || lastConfirmedOrder.order_id}
          </h2>

          <p className="text-xs text-slate-300 mt-1">
            Заявка передана на центральный склад и ожидает сборки
          </p>
        </div>

        {/* Order Details Body */}
        <div className="p-5 overflow-y-auto space-y-4 no-scrollbar flex-1">
          {/* Metadata Cards */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-3 rounded-2xl bg-slate-800/60 border border-slate-700/50">
              <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-slate-400 mb-1">
                <Store className="w-3.5 h-3.5 text-brand-400" />
                <span>Точка (Бар)</span>
              </div>
              <div className="text-xs font-bold text-slate-100 truncate">
                {selectedBar.name}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-slate-800/60 border border-slate-700/50">
              <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-slate-400 mb-1">
                <Clock className="w-3.5 h-3.5 text-emerald-400" />
                <span>Статус</span>
              </div>
              <div className="text-xs font-bold text-emerald-400 capitalize">
                В обработке
              </div>
            </div>
          </div>

          {/* Confirmed Items List */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-slate-300 px-1">
              <div className="flex items-center gap-1.5">
                <PackageCheck className="w-4 h-4 text-brand-400" />
                <span>Забронированные позиции ({lastConfirmedOrder.items.length})</span>
              </div>
              <span className="text-slate-400 font-medium text-[11px]">
                Всего: {totalConfirmedUnits} ед.
              </span>
            </div>

            <div className="space-y-1.5 max-h-56 overflow-y-auto no-scrollbar">
              {lastConfirmedOrder.items.map((item) => (
                <div
                  key={item.id || item.product_id}
                  className="p-2.5 rounded-xl bg-slate-800/70 border border-slate-700/50 flex items-center justify-between gap-2"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px] font-mono text-slate-400 bg-slate-900/60 px-1.5 py-0.5 rounded">
                        {item.sku}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {item.unit}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-slate-200 truncate mt-0.5">
                      {item.name}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-1 rounded-lg">
                      {item.confirmed_qty} {item.unit}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span>Оформлено: {formattedDate}</span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 shrink-0">
          <button
            onClick={handleClose}
            className="w-full py-3.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 active:scale-[0.98] text-white font-bold text-sm shadow-xl shadow-brand-600/30 flex items-center justify-center gap-2 transition-all"
          >
            <span>Сделать новый заказ</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
