import React from 'react';
import { SearchX, Sparkles } from 'lucide-react';
import { Product, CategoryGroup } from '../types/catalog';
import { ProductCard } from './ProductCard';

interface ProductListProps {
  categories: CategoryGroup[];
  activeCategory: string | null;
  searchQuery: string;
  onClearSearch: () => void;
}

export const ProductList: React.FC<ProductListProps> = ({
  categories,
  activeCategory,
  searchQuery,
  onClearSearch,
}) => {
  const query = searchQuery.trim().toLowerCase();

  // Filter products
  const getFilteredGroups = (): CategoryGroup[] => {
    let filtered = categories;

    // Filter by active category if selected
    if (activeCategory) {
      filtered = filtered.filter((c) => c.category === activeCategory);
    }

    // Filter by search query if present
    if (query) {
      filtered = filtered
        .map((cat) => ({
          ...cat,
          items: cat.items.filter(
            (p: Product) =>
              p.name.toLowerCase().includes(query) ||
              p.sku.toLowerCase().includes(query) ||
              p.unit.toLowerCase().includes(query)
          ),
        }))
        .filter((cat) => cat.items.length > 0);
    }

    return filtered;
  };

  const filteredGroups = getFilteredGroups();
  const totalFoundProducts = filteredGroups.reduce(
    (sum, g) => sum + g.items.length,
    0
  );

  if (filteredGroups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
        <div className="w-16 h-16 rounded-2xl bg-tg-secondaryBg flex items-center justify-center text-tg-hint mb-4">
          <SearchX className="w-8 h-8" />
        </div>
        <h4 className="text-base font-bold text-tg-text mb-1">
          Ничего не найдено
        </h4>
        <p className="text-xs text-tg-hint max-w-xs mb-5">
          По запросу «{searchQuery}» в категории «{activeCategory || 'Все'}»
          товаров не обнаружено.
        </p>
        <button
          onClick={onClearSearch}
          className="px-4 py-2 rounded-md bg-tg-secondaryBg hover:bg-brand-50 text-tg-text text-xs font-semibold tap-active transition-colors"
        >
          Сбросить поиск
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 py-4 space-y-6 pb-28">
      {/* If searching, display search summary */}
      {query && (
        <div className="flex items-center justify-between text-xs text-tg-hint bg-tg-secondaryBg px-3 py-2 rounded-md">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-brand-500" />
            <span>
              Результаты поиска: <b className="text-tg-text">{totalFoundProducts}</b> поз.
            </span>
          </div>
          <button
            onClick={onClearSearch}
            className="text-brand-600 font-semibold hover:underline"
          >
            Очистить
          </button>
        </div>
      )}

      {/* Render groups */}
      {filteredGroups.map((group) => (
        <section key={group.category} className="space-y-3">
          {/* Section Category Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-tg-text flex items-center gap-2">
              <span className="w-1.5 h-4 bg-brand-500 rounded-sm inline-block"></span>
              {group.category}
            </h2>
            <span className="text-[11px] font-medium text-tg-hint px-2 py-0.5 rounded-md bg-tg-secondaryBg">
              {group.items.length} {group.items.length === 1 ? 'позиция' : 'позиций'}
            </span>
          </div>

          {/* Grid of Product Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {group.items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
};
