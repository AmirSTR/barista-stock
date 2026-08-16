import React from 'react';
import { ShoppingBag, ArrowRight } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { telegram } from '../services/telegram';

export const FloatingCartBar: React.FC = () => {
  const {
    totalPositionsCount,
    totalQuantity,
    setIsCartOpen,
    isCartOpen,
  } = useCart();

  if (totalPositionsCount === 0 || isCartOpen) {
    return null;
  }

  const handleOpenCart = () => {
    telegram.hapticImpact('medium');
    setIsCartOpen(true);
  };

  return (
    <div className="fixed bottom-4 left-4 right-4 z-40 animate-slide-up">
      <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700/80 shadow-2xl rounded-2xl p-2.5 flex items-center justify-between gap-3 max-w-md mx-auto ring-1 ring-white/10">
        {/* Left: Summary Info */}
        <div className="flex items-center gap-3 pl-2">
          <div className="relative">
            <div className="w-11 h-11 rounded-xl bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-brand-400">
              <ShoppingBag className="w-5 h-5" />
            </div>
            <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-brand-500 text-white text-[11px] font-extrabold rounded-full flex items-center justify-center shadow-md animate-bounce-subtle">
              {totalPositionsCount}
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-xs font-bold text-slate-100 leading-tight">
              {totalPositionsCount}{' '}
              {totalPositionsCount === 1
                ? 'позиция'
                : totalPositionsCount < 5
                ? 'позиции'
                : 'позиций'}
            </span>
            <span className="text-[11px] text-slate-400 font-medium">
              Всего: <b className="text-brand-300 font-semibold">{totalQuantity}</b> ед.
            </span>
          </div>
        </div>

        {/* Right: Open Cart Button */}
        <button
          onClick={handleOpenCart}
          className="flex items-center gap-2 py-3 px-5 rounded-xl bg-brand-600 hover:bg-brand-500 active:scale-95 text-white font-bold text-xs shadow-lg shadow-brand-600/30 transition-all shrink-0"
        >
          <span>Корзина</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
