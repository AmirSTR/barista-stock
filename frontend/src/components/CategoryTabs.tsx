import React, { useRef, useEffect } from 'react';
import {
  CupSoda,
  Coffee,
  Droplet,
  Sparkles,
  Milk,
  Cookie,
  Package,
  Sparkle,
  LayoutGrid,
} from 'lucide-react';
import { telegram } from '../services/telegram';

interface CategoryTabsProps {
  categories: Array<{ category: string; items_count: number }>;
  activeCategory: string | null;
  onSelectCategory: (categoryName: string | null) => void;
  totalProductsCount: number;
}

export const CategoryTabs: React.FC<CategoryTabsProps> = ({
  categories,
  activeCategory,
  onSelectCategory,
  totalProductsCount,
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const activeTabRef = useRef<HTMLButtonElement>(null);

  // Auto scroll active tab into view
  useEffect(() => {
    if (activeTabRef.current && scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      const tab = activeTabRef.current;
      const containerLeft = container.scrollLeft;
      const containerWidth = container.clientWidth;
      const tabLeft = tab.offsetLeft;
      const tabWidth = tab.clientWidth;

      if (
        tabLeft < containerLeft ||
        tabLeft + tabWidth > containerLeft + containerWidth
      ) {
        container.scrollTo({
          left: tabLeft - containerWidth / 2 + tabWidth / 2,
          behavior: 'smooth',
        });
      }
    }
  }, [activeCategory]);

  const getCategoryIcon = (categoryName: string) => {
    switch (categoryName) {
      case 'Стаканы и крышки':
        return <CupSoda className="w-4 h-4" />;
      case 'Кофе, Чай, Дрипы':
        return <Coffee className="w-4 h-4" />;
      case 'Сиропы':
        return <Droplet className="w-4 h-4" />;
      case 'Основы и порошки':
        return <Sparkles className="w-4 h-4" />;
      case 'Молоко и напитки':
        return <Milk className="w-4 h-4" />;
      case 'Десерты и выпечка':
        return <Cookie className="w-4 h-4" />;
      case 'Расходники и упаковка':
        return <Package className="w-4 h-4" />;
      case 'Химия и хозтовары':
        return <Sparkle className="w-4 h-4" />;
      default:
        return <LayoutGrid className="w-4 h-4" />;
    }
  };

  const handleTabClick = (categoryName: string | null) => {
    telegram.hapticImpact('light');
    onSelectCategory(categoryName);
  };

  return (
    <div className="sticky top-[108px] z-20 bg-slate-900/95 backdrop-blur-md border-b border-slate-800/60 py-2.5 shadow-sm">
      <div
        ref={scrollContainerRef}
        className="flex items-center gap-2 px-4 overflow-x-auto no-scrollbar scroll-smooth"
      >
        {/* "All" Tab */}
        <button
          ref={activeCategory === null ? activeTabRef : null}
          onClick={() => handleTabClick(null)}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-200 shrink-0 ${
            activeCategory === null
              ? 'bg-brand-500 text-white shadow-md shadow-brand-500/25 scale-[1.02]'
              : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700/50'
          }`}
        >
          <LayoutGrid className="w-3.5 h-3.5" />
          <span>Все</span>
          <span
            className={`text-[10px] px-1.5 py-0.2 rounded-full ml-0.5 ${
              activeCategory === null
                ? 'bg-white/20 text-white'
                : 'bg-slate-700 text-slate-400'
            }`}
          >
            {totalProductsCount}
          </span>
        </button>

        {/* 8 Categories */}
        {categories.map((cat) => {
          const isActive = activeCategory === cat.category;
          return (
            <button
              key={cat.category}
              ref={isActive ? activeTabRef : null}
              onClick={() => handleTabClick(cat.category)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-200 shrink-0 ${
                isActive
                  ? 'bg-brand-500 text-white shadow-md shadow-brand-500/25 scale-[1.02]'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white border border-slate-700/50'
              }`}
            >
              {getCategoryIcon(cat.category)}
              <span>{cat.category}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ml-0.5 ${
                  isActive
                    ? 'bg-white/20 text-white'
                    : 'bg-slate-700 text-slate-400'
                }`}
              >
                {cat.items_count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
