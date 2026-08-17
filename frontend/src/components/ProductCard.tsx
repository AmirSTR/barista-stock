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
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-[10px] font-bold bg-red-100 text-red-600">
          <Ban className="w-3 h-3" />
          В СТОПЕ
        </span>
      );
    }

    if (product.available_qty <= 5) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-[10px] font-bold bg-amber-100 text-amber-600">
          <AlertCircle className="w-3 h-3" />
          Мало: {product.available_qty} {product.unit}
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-[10px] font-bold bg-brand-50 text-brand-600">
        <Check className="w-3 h-3" />
        Доступно: {product.available_qty} {product.unit}
      </span>
    );
  };

  return (
    <div
      className={`relative flex flex-col justify-between p-3.5 rounded-xl transition-colors duration-200 ${
        isStop
          ? 'bg-tg-bg opacity-60 grayscale-[40%] border border-tg-secondaryBg'
          : currentQuantity > 0
          ? 'bg-tg-bg border-2 border-brand-500 shadow-[0_4px_12px_rgba(96,108,56,0.1)]'
          : 'bg-tg-bg border border-tg-secondaryBg hover:border-brand-200'
      }`}
    >
      {/* Top Meta: SKU & Stock Badge */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className="text-[10px] font-mono font-medium text-tg-hint tracking-wider">
            {product.sku}
          </span>
          {getStockBadge()}
        </div>

        {/* Product Title */}
        <h3
          className={`text-sm font-semibold leading-snug line-clamp-2 mb-1 ${
            isStop ? 'text-tg-hint line-through decoration-red-400' : 'text-tg-text'
          }`}
          title={product.name}
        >
          {product.name}
        </h3>

        {/* Unit & Category */}
        <div className="flex items-center gap-2 text-xs text-tg-hint mb-3">
          <span className="px-2 py-0.5 rounded-md bg-tg-secondaryBg text-[11px] font-medium text-tg-text">
            {product.unit}
          </span>
          <span className="text-[11px] truncate">
            {product.category}
          </span>
        </div>
      </div>

      {/* Action / Stepper Controls */}
      <div className="mt-2 pt-3 border-t border-tg-secondaryBg flex items-center justify-between gap-2">
        {isStop ? (
          <button
            disabled
            className="w-full py-2 px-3 rounded-md bg-tg-secondaryBg text-tg-hint text-xs font-semibold flex items-center justify-center gap-1.5 cursor-not-allowed"
          >
            <Ban className="w-3.5 h-3.5" />
            Недоступно
          </button>
        ) : currentQuantity === 0 ? (
          <button
            onClick={handleAdd}
            className="w-full py-2 px-3 rounded-md bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold flex items-center justify-center gap-1.5 tap-active transition-colors"
          >
            <Plus className="w-4 h-4" />
            В заказ
          </button>
        ) : (
          <div className="flex items-center justify-between w-full bg-brand-50 rounded-md p-1 border border-brand-200">
            {/* Decrement Button */}
            <button
              onClick={handleDecrement}
              className="w-8 h-8 rounded text-brand-600 hover:bg-brand-100 flex items-center justify-center transition-colors tap-active"
            >
              <Minus className="w-4 h-4" />
            </button>

            {/* Current Qty & Max cue */}
            <div className="flex flex-col items-center px-2">
              <span className="text-sm font-bold text-brand-700 leading-tight">
                {currentQuantity}
              </span>
              <span className="text-[9px] font-medium text-brand-500 leading-none">
                из {product.available_qty}
              </span>
            </div>

            {/* Increment Button */}
            <button
              onClick={handleAdd}
              disabled={isLimitReached}
              className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
                isLimitReached
                  ? 'text-brand-300 cursor-not-allowed'
                  : 'bg-brand-500 text-white hover:bg-brand-600 tap-active'
              }`}
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Limit Reached Warning Label */}
      {isLimitReached && currentQuantity > 0 && (
        <div className="text-[10px] text-amber-600 font-medium text-center mt-1.5">
          Максимум на складе
        </div>
      )}
    </div>
  );
};
