import React from 'react';
import { Search, X, MapPin, Store, Sparkles } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { telegram } from '../services/telegram';

interface HeaderProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  totalProductsCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  searchQuery,
  setSearchQuery,
  totalProductsCount,
}) => {
  const { selectedBar, setIsBarSelectorOpen } = useCart();
  const tgUser = telegram.getUser();

  const handleClearSearch = () => {
    setSearchQuery('');
    telegram.hapticImpact('light');
  };

  return (
    <header className="sticky top-0 z-30 bg-tg-bg border-b border-tg-secondaryBg px-4 pt-3 pb-3 transition-colors">
      {/* Top Bar: Location & Profile */}
      <div className="flex items-center justify-between gap-2 mb-3">
        {/* Bar Selector Button */}
        <button
          onClick={() => {
            telegram.hapticImpact('light');
            setIsBarSelectorOpen(true);
          }}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-tg-secondaryBg hover:bg-brand-50 border border-transparent active:border-brand-200 transition-all text-left max-w-[70%] tap-active"
        >
          <div className="w-6 h-6 rounded-md bg-brand-100 text-brand-600 flex items-center justify-center shrink-0">
            <Store className="w-3.5 h-3.5" />
          </div>
          <div className="truncate">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-tg-hint leading-tight">
              Точка заказа
            </div>
            <div className="text-xs font-bold text-tg-text truncate">
              {selectedBar.name}
            </div>
          </div>
          <MapPin className="w-3.5 h-3.5 text-brand-500 ml-0.5 shrink-0" />
        </button>

        {/* User Info / Badge */}
        <div className="flex items-center gap-2">
          {tgUser ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-tg-secondaryBg border border-transparent text-xs font-medium text-tg-text">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="truncate max-w-[80px]">
                {tgUser.first_name}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-tg-secondaryBg border border-transparent text-[11px] font-medium text-tg-hint">
              <Sparkles className="w-3 h-3 text-brand-500" />
              <span>{totalProductsCount} SKU</span>
            </div>
          )}
        </div>
      </div>

      {/* Search Input Bar */}
      <div className="relative flex items-center">
        <div className="absolute left-3.5 pointer-events-none text-tg-hint">
          <Search className="w-4 h-4" />
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Поиск по названию или артикулу..."
          className="w-full pl-10 pr-10 py-2.5 bg-tg-secondaryBg text-tg-text placeholder-tg-hint text-sm rounded-md border border-transparent focus:border-brand-500 focus:bg-tg-bg focus:outline-none transition-all"
        />
        {searchQuery && (
          <button
            onClick={handleClearSearch}
            className="absolute right-3 p-1 rounded-md text-tg-hint hover:text-tg-text active:scale-95 transition-transform"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  );
};
