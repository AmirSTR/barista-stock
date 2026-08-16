import React, { useEffect, useState, useCallback } from 'react';
import { Loader2, RefreshCw, AlertCircle } from 'lucide-react';
import { ApiService } from './services/api';
import { telegram } from './services/telegram';
import { CatalogResponse } from './types/catalog';
import { CartProvider } from './context/CartContext';
import { Header } from './components/Header';
import { CategoryTabs } from './components/CategoryTabs';
import { ProductList } from './components/ProductList';
import { FloatingCartBar } from './components/FloatingCartBar';
import { CartDrawer } from './components/CartDrawer';
import { StockAlertModal } from './components/StockAlertModal';
import { SuccessOrderModal } from './components/SuccessOrderModal';
import { BarSelectorModal } from './components/BarSelectorModal';

const MainCatalogApp: React.FC = () => {
  const [catalogData, setCatalogData] = useState<CatalogResponse | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCatalog = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setIsRefreshing(true);
    else setIsLoading(true);
    setError(null);

    try {
      const data = await ApiService.getCatalog();
      setCatalogData(data);
    } catch (err) {
      console.error('Failed to load catalog:', err);
      setError('Не удалось загрузить каталог товаров');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    // Initialize Telegram WebApp SDK
    telegram.init();
    fetchCatalog();
  }, [fetchCatalog]);

  const handleClearSearch = () => {
    setSearchQuery('');
  };

  const handleRefresh = () => {
    telegram.hapticImpact('light');
    fetchCatalog(true);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-14 h-14 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 mb-4 animate-pulse">
          <Loader2 className="w-7 h-7 animate-spin" />
        </div>
        <h3 className="text-base font-bold text-slate-100">
          Загрузка каталога склада...
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Синхронизация остатков с сервером сети
        </p>
      </div>
    );
  }

  if (error || !catalogData) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mb-4">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-slate-100 mb-1">
          Ошибка подключения
        </h3>
        <p className="text-xs text-slate-400 max-w-xs mb-5">
          {error || 'Не удалось получить актуальные данные склада'}
        </p>
        <button
          onClick={() => fetchCatalog()}
          className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-lg shadow-brand-600/30 flex items-center gap-2 active:scale-95 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Повторить попытку</span>
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative selection:bg-brand-500/30">
      {/* 1. Top Header with Bar Selector & Search */}
      <Header
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        totalProductsCount={catalogData.total_products}
      />

      {/* 2. 8 Categories Horizontal Scrollable Tabs */}
      <CategoryTabs
        categories={catalogData.categories}
        activeCategory={activeCategory}
        onSelectCategory={setActiveCategory}
        totalProductsCount={catalogData.total_products}
      />

      {/* 3. Main Product List with Stop-states & Steppers */}
      <main className="flex-1">
        <ProductList
          categories={catalogData.categories}
          activeCategory={activeCategory}
          searchQuery={searchQuery}
          onClearSearch={handleClearSearch}
        />
      </main>

      {/* 4. Floating Cart Summary Bar */}
      <FloatingCartBar />

      {/* 5. Cart Drawer & Checkout Screen */}
      <CartDrawer />

      {/* 6. Stock Alert Modal (Handles Concurrent Stock Drops / Out of Stock) */}
      <StockAlertModal />

      {/* 7. Success Order Modal with Confirmation Details */}
      <SuccessOrderModal />

      {/* 8. Bar Selector Modal */}
      <BarSelectorModal />

      {/* Refresh Floating Action Button for Testing */}
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className={`fixed top-3.5 right-4 z-40 p-2 rounded-xl bg-slate-800/80 border border-slate-700/80 text-slate-400 hover:text-slate-200 active:scale-90 transition-all ${
          isRefreshing ? 'animate-spin text-brand-400' : ''
        }`}
        title="Обновить остатки"
      >
        <RefreshCw className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <CartProvider>
      <MainCatalogApp />
    </CartProvider>
  );
};

export default App;
