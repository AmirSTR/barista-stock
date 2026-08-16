import { TelegramWebApp, TelegramUser } from '../types/telegram';

class TelegramService {
  private webApp: TelegramWebApp | null = null;
  private isAvailable: boolean = false;
  private clickCallbacks: Array<() => void> = [];
  private backClickCallbacks: Array<() => void> = [];

  constructor() {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      this.webApp = window.Telegram.WebApp;
      this.isAvailable = Boolean(this.webApp.initData || this.webApp.version);
    }
  }

  public init(): void {
    if (!this.webApp) {
      console.log('📱 Telegram WebApp SDK not detected; running in mock/browser mode');
      return;
    }

    try {
      this.webApp.ready();
      this.webApp.expand();
      if (typeof this.webApp.enableClosingConfirmation === 'function') {
        this.webApp.enableClosingConfirmation();
      }
      this.applyTheme();
      this.webApp.onEvent('themeChanged', () => {
        this.applyTheme();
      });
    } catch (e) {
      console.warn('⚠️ Telegram WebApp initialization warning:', e);
    }
  }

  public isTelegramEnvironment(): boolean {
    return this.isAvailable;
  }

  public getWebApp(): TelegramWebApp | null {
    return this.webApp;
  }

  public getUser(): TelegramUser | null {
    return this.webApp?.initDataUnsafe?.user || null;
  }

  public getInitData(): string {
    return this.webApp?.initData || '';
  }

  public getStartParam(): string | null {
    return this.webApp?.initDataUnsafe?.start_param || null;
  }

  public isExpanded(): boolean {
    return this.webApp?.isExpanded ?? true;
  }

  public expand(): void {
    if (this.webApp?.expand) {
      this.webApp.expand();
    }
  }

  public close(): void {
    if (this.webApp?.close) {
      this.webApp.close();
    }
  }

  // --- Theme Sync ---
  public applyTheme(): void {
    if (!this.webApp) return;

    const themeParams = this.webApp.themeParams || {};
    const root = document.documentElement;

    if (themeParams.bg_color) {
      root.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
    }
    if (themeParams.secondary_bg_color) {
      root.style.setProperty('--tg-theme-secondary-bg-color', themeParams.secondary_bg_color);
    }
    if (themeParams.text_color) {
      root.style.setProperty('--tg-theme-text-color', themeParams.text_color);
    }
    if (themeParams.hint_color) {
      root.style.setProperty('--tg-theme-hint-color', themeParams.hint_color);
    }
    if (themeParams.link_color) {
      root.style.setProperty('--tg-theme-link-color', themeParams.link_color);
    }
    if (themeParams.button_color) {
      root.style.setProperty('--tg-theme-button-color', themeParams.button_color);
    }
    if (themeParams.button_text_color) {
      root.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color);
    }

    if (this.webApp.colorScheme === 'light') {
      root.classList.add('tg-theme-light');
    } else {
      root.classList.remove('tg-theme-light');
    }
  }

  // --- MainButton Binding ---
  public setupMainButton(config: {
    text: string;
    onClick: () => void;
    isVisible?: boolean;
    isActive?: boolean;
    color?: string;
    textColor?: string;
  }): void {
    if (!this.webApp?.MainButton) return;

    const mb = this.webApp.MainButton;
    
    // Clear previous callbacks
    this.clearMainButtonClick();

    mb.setText(config.text);
    if (config.color) mb.setParams({ color: config.color });
    if (config.textColor) mb.setParams({ text_color: config.textColor });

    const handler = () => {
      config.onClick();
    };
    this.clickCallbacks.push(handler);
    mb.onClick(handler);

    if (config.isActive !== false) {
      mb.enable();
    } else {
      mb.disable();
    }

    if (config.isVisible !== false) {
      mb.show();
    } else {
      mb.hide();
    }
  }

  public showMainButton(): void {
    if (this.webApp?.MainButton) {
      this.webApp.MainButton.show();
    }
  }

  public hideMainButton(): void {
    if (this.webApp?.MainButton) {
      this.webApp.MainButton.hide();
    }
  }

  public setMainButtonLoading(isLoading: boolean): void {
    if (!this.webApp?.MainButton) return;
    if (isLoading) {
      this.webApp.MainButton.showProgress(false);
      this.webApp.MainButton.disable();
    } else {
      this.webApp.MainButton.hideProgress();
      this.webApp.MainButton.enable();
    }
  }

  public clearMainButtonClick(): void {
    if (!this.webApp?.MainButton) return;
    for (const cb of this.clickCallbacks) {
      this.webApp.MainButton.offClick(cb);
    }
    this.clickCallbacks = [];
  }

  // --- BackButton Binding ---
  public setupBackButton(onBack: () => void): void {
    if (!this.webApp?.BackButton) return;
    
    this.clearBackButtonClick();
    const handler = () => {
      onBack();
    };
    this.backClickCallbacks.push(handler);
    this.webApp.BackButton.onClick(handler);
    this.webApp.BackButton.show();
  }

  public hideBackButton(): void {
    if (!this.webApp?.BackButton) return;
    this.clearBackButtonClick();
    this.webApp.BackButton.hide();
  }

  public clearBackButtonClick(): void {
    if (!this.webApp?.BackButton) return;
    for (const cb of this.backClickCallbacks) {
      this.webApp.BackButton.offClick(cb);
    }
    this.backClickCallbacks = [];
  }

  // --- Haptic Feedback ---
  public hapticImpact(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'light'): void {
    try {
      if (this.webApp?.HapticFeedback?.impactOccurred) {
        this.webApp.HapticFeedback.impactOccurred(style);
      } else if (typeof navigator !== 'undefined' && navigator.vibrate) {
        navigator.vibrate(10);
      }
    } catch {
      // ignore in unsupported browsers
    }
  }

  public hapticNotification(type: 'error' | 'success' | 'warning'): void {
    try {
      if (this.webApp?.HapticFeedback?.notificationOccurred) {
        this.webApp.HapticFeedback.notificationOccurred(type);
      } else if (typeof navigator !== 'undefined' && navigator.vibrate) {
        if (type === 'success') navigator.vibrate([15, 30, 20]);
        else if (type === 'warning') navigator.vibrate([20, 50, 20]);
        else navigator.vibrate([50, 50, 50]);
      }
    } catch {
      // ignore
    }
  }

  public hapticSelection(): void {
    try {
      if (this.webApp?.HapticFeedback?.selectionChanged) {
        this.webApp.HapticFeedback.selectionChanged();
      }
    } catch {
      // ignore
    }
  }
}

export const telegram = new TelegramService();
