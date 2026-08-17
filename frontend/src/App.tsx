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
      <div className="min-h-screen bg-tg-bg flex flex-col items-center justify-center p-6 text-center">
        <div className="w-14 h-14 rounded-xl bg-brand-100 flex items-center justify-center text-brand-600 mb-4 animate-spin">
          <Loader2 className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-tg-text">
          Загрузка каталога склада...
        </h3>
        <p className="text-xs text-tg-hint mt-1">
          Синхронизация остатков с сервером сети
        </p>
      </div>
    );
  }

  if (error || !catalogData) {
    return (
      <div className="min-h-screen bg-tg-bg flex flex-col items-center justify-center p-6 text-center">
        <div className="w-14 h-14 rounded-xl bg-red-50 flex items-center justify-center text-red-500 mb-4">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-tg-text mb-1">
          Ошибка подключения
        </h3>
        <p className="text-xs text-tg-hint max-w-xs mb-5">
          {error || 'Не удалось получить актуальные данные склада'}
        </p>
        <button
          onClick={() => fetchCatalog()}
          className="px-5 py-2.5 rounded-md bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold flex items-center gap-2 transition-colors tap-active"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Повторить попытку</span>
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-tg-bg text-tg-text flex flex-col relative selection:bg-brand-100">
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
        className={`fixed top-3.5 right-4 z-40 p-2 rounded-md bg-tg-secondaryBg text-tg-hint hover:text-brand-500 transition-colors tap-active ${
          isRefreshing ? 'animate-spin text-brand-500' : ''
        }`}
        title="Обновить остатки"
      >
        <RefreshCw className="w-4 h-4" />
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
