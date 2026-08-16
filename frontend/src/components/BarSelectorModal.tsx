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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="w-full max-w-sm bg-slate-900 border border-slate-700/80 rounded-3xl shadow-2xl overflow-hidden animate-slide-up flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-brand-500/20 text-brand-400 flex items-center justify-center">
              <Store className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-white">
              Выберите точку (Бар)
            </h3>
          </div>
          <button
            onClick={() => {
              telegram.hapticImpact('light');
              setIsBarSelectorOpen(false);
            }}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* List of Bars */}
        <div className="p-4 space-y-2 max-h-72 overflow-y-auto no-scrollbar">
          {isBarsLoading && (
            <div className="flex items-center justify-center gap-2 py-8 text-xs text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Загрузка кофеен...</span>
            </div>
          )}

          {!isBarsLoading && barsError && (
            <div className="flex items-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
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
                className={`w-full flex items-center justify-between p-3 rounded-2xl border transition-all text-left ${
                  isSelected
                    ? 'bg-brand-500/15 border-brand-500/50 shadow-md shadow-brand-500/10'
                    : 'bg-slate-800/60 border-slate-700/50 hover:bg-slate-800 hover:border-slate-600'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                      isSelected
                        ? 'bg-brand-500 text-white'
                        : 'bg-slate-700/60 text-slate-400'
                    }`}
                  >
                    <MapPin className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-100">
                      {bar.name}
                    </div>
                    {bar.address && (
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {bar.address}
                      </div>
                    )}
                  </div>
                </div>

                {isSelected && (
                  <div className="w-6 h-6 rounded-full bg-brand-500 text-white flex items-center justify-center shrink-0">
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
