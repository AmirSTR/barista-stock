import React from 'react';
import { Store, Check, X, MapPin, Loader2, AlertCircle } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { CoffeeBar } from '../types/catalog';
import { telegram } from '../services/telegram';

export const BarSelectorModal: React.FC = () => {
  const {
    isBarSelectorOpen,
    setIsBarSelectorOpen,
    selectedBar,
    setSelectedBar,
    bars,
    isBarsLoading,
    barsError,
  } = useCart();

  if (!isBarSelectorOpen) return null;

  const handleSelectBar = (bar: CoffeeBar) => {
    telegram.hapticImpact('medium');
    setSelectedBar(bar);
    setIsBarSelectorOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-sm bg-tg-bg border border-tg-secondaryBg rounded-2xl shadow-xl overflow-hidden animate-slide-up flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-tg-secondaryBg">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-100 text-brand-600 flex items-center justify-center">
              <Store className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-tg-text">
              Выберите точку (Бар)
            </h3>
          </div>
          <button
            onClick={() => {
              telegram.hapticImpact('light');
              setIsBarSelectorOpen(false);
            }}
            className="p-1.5 rounded-md text-tg-hint hover:text-tg-text hover:bg-tg-secondaryBg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* List of Bars */}
        <div className="p-4 space-y-2 max-h-72 overflow-y-auto no-scrollbar">
          {isBarsLoading && (
            <div className="flex items-center justify-center gap-2 py-8 text-xs text-tg-hint">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Загрузка кофеен...</span>
            </div>
          )}

          {!isBarsLoading && barsError && (
            <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-xs text-red-600">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{barsError}</span>
            </div>
          )}

          {!isBarsLoading && !barsError && bars.map((bar) => {
            const isSelected = bar.id === selectedBar.id;
            return (
              <button
                key={bar.id}
                onClick={() => handleSelectBar(bar)}
                className={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors text-left tap-active ${
                  isSelected
                    ? 'bg-brand-50 border-brand-500 shadow-[0_2px_8px_rgba(96,108,56,0.1)]'
                    : 'bg-tg-secondaryBg border-transparent hover:bg-brand-50 hover:border-brand-200'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <div
                    className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 ${
                      isSelected
                        ? 'bg-brand-500 text-white'
                        : 'bg-tg-bg text-tg-hint'
                    }`}
                  >
                    <MapPin className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-tg-text">
                      {bar.name}
                    </div>
                    {bar.address && (
                      <div className="text-[11px] text-tg-hint mt-0.5">
                        {bar.address}
                      </div>
                    )}
                  </div>
                </div>

                {isSelected && (
                  <div className="w-6 h-6 rounded-md bg-brand-500 text-white flex items-center justify-center shrink-0">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
