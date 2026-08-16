import React from 'react';
import { Plus, Minus, Ban, Check, AlertCircle } from 'lucide-react';
import { Product } from '../types/catalog';
import { useCart } from '../context/CartContext';
import { telegram } from '../services/telegram';

interface ProductCardProps {
  product: Product;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const { addItem, decrementItem, getItemQuantity } = useCart();
  const currentQuantity = getItemQuantity(product.id);
  const isStop = product.is_stop || product.available_qty <= 0;
  const isLimitReached = !isStop && currentQuantity >= product.available_qty;

  const handleAdd = () => {
    if (isStop) {
      telegram.hapticNotification('warning');
      return;
    }
    if (isLimitReached) {
      telegram.hapticNotification('warning');
      return;
    }
    addItem(product, 1);
  };

  const handleDecrement = () => {
    decrementItem(product.id);
  };

  // Stock badge styling
  const getStockBadge = () => {
    if (isStop) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
          <Ban className="w-3 h-3" />
          В СТОПЕ
        </span>
      );
    }

    if (product.available_qty <= 5) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
          <AlertCircle className="w-3 h-3" />
          Мало: {product.available_qty} {product.unit}
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
        <Check className="w-3 h-3" />
        Доступно: {product.available_qty} {product.unit}
      </span>
    );
  };

  return (
    <div
      className={`relative flex flex-col justify-between p-3.5 rounded-2xl border transition-all duration-200 ${
        isStop
          ? 'bg-slate-900/40 border-slate-800/40 opacity-60 grayscale-[40%]'
          : currentQuantity > 0
          ? 'bg-slate-800/90 border-brand-500/50 shadow-md shadow-brand-500/10'
          : 'bg-slate-800/70 border-slate-700/60 hover:border-slate-600/80 shadow-sm'
      }`}
    >
      {/* Top Meta: SKU & Stock Badge */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className="text-[10px] font-mono font-medium text-slate-400 tracking-wider">
            {product.sku}
          </span>
          {getStockBadge()}
        </div>

        {/* Product Title */}
        <h3
          className={`text-sm font-semibold leading-snug line-clamp-2 mb-1 ${
            isStop ? 'text-slate-400 line-through decoration-rose-500/50' : 'text-slate-100'
          }`}
          title={product.name}
        >
          {product.name}
        </h3>

        {/* Unit & Category */}
        <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
          <span className="px-2 py-0.5 rounded bg-slate-900/60 border border-slate-700/40 text-[11px] font-medium text-slate-300">
            {product.unit}
          </span>
          <span className="text-[11px] text-slate-400 truncate">
            {product.category}
          </span>
        </div>
      </div>

      {/* Action / Stepper Controls */}
      <div className="mt-2 pt-2 border-t border-slate-700/40 flex items-center justify-between gap-2">
        {isStop ? (
          <button
            disabled
            className="w-full py-2 px-3 rounded-xl bg-slate-800/60 text-slate-500 text-xs font-semibold flex items-center justify-center gap-1.5 cursor-not-allowed border border-slate-800"
          >
            <Ban className="w-3.5 h-3.5" />
            Недоступно
          </button>
        ) : currentQuantity === 0 ? (
          <button
            onClick={handleAdd}
            className="w-full py-2 px-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 active:scale-95 transition-all shadow-sm shadow-brand-600/30"
          >
            <Plus className="w-4 h-4" />
            В заказ
          </button>
        ) : (
          <div className="flex items-center justify-between w-full bg-slate-900/80 rounded-xl p-1 border border-brand-500/40">
            {/* Decrement Button */}
            <button
              onClick={handleDecrement}
              className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 active:scale-90 flex items-center justify-center text-slate-200 hover:text-white transition-all"
            >
              <Minus className="w-4 h-4" />
            </button>

            {/* Current Qty & Max cue */}
            <div className="flex flex-col items-center px-2">
              <span className="text-sm font-bold text-white leading-tight">
                {currentQuantity}
              </span>
              <span className="text-[9px] font-medium text-slate-400 leading-none">
                из {product.available_qty}
              </span>
            </div>

            {/* Increment Button */}
            <button
              onClick={handleAdd}
              disabled={isLimitReached}
              className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                isLimitReached
                  ? 'bg-slate-800/40 text-slate-600 cursor-not-allowed'
                  : 'bg-brand-600 hover:bg-brand-500 active:scale-90 text-white'
              }`}
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Limit Reached Warning Label */}
      {isLimitReached && currentQuantity > 0 && (
        <div className="text-[10px] text-amber-400 font-medium text-center mt-1">
          Максимум на складе
        </div>
      )}
    </div>
  );
};
