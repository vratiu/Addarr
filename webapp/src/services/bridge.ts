import { ref, set, onValue, off, remove } from 'firebase/database';
import { signInWithCustomToken } from 'firebase/auth';
import { database, auth } from './firebase';
import { SearchResult, LibraryItem, AppConfigOptions, CalendarItem, MediaType } from '../types';

declare global {
  interface Window {
    Telegram?: {
      WebApp?: any;
    };
  }
}

export class BridgeService {
  private userId: string;
  private username: string;
  private initData: string;

  constructor() {
    const tg = window.Telegram?.WebApp;
    const tgUser = tg?.initDataUnsafe?.user;
    this.userId = String(tgUser?.id || 'demo_user_123');
    this.username = tgUser?.username || '';
    this.initData = tg?.initData || '';
  }

  public getUserId(): string {
    return this.userId;
  }

  public getUsername(): string {
    return this.username;
  }

  /**
   * Optional exchange of Telegram initData for Firebase Auth token
   */
  public async authenticate(authEndpoint?: string): Promise<boolean> {
    if (!authEndpoint || !this.initData) {
      return true;
    }
    try {
      const res = await fetch(authEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: this.initData }),
      });
      const data = await res.json();
      if (data.token) {
        await signInWithCustomToken(auth, data.token);
        return true;
      }
    } catch (e) {
      console.warn('Firebase custom token authentication failed, falling back:', e);
    }
    return false;
  }

  private generateRequestId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
      const bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
    }
    return `${Date.now()}_${Math.random().toString(36).substring(2, 12)}`;
  }

  /**
   * Dispatches an action over Firebase RTDB and waits for Addarr's response.
   */
  public async sendCommand<T = any>(action: string, payload: Record<string, any> = {}): Promise<T> {
    const reqId = this.generateRequestId();
    const requestRef = ref(database, `requests/${this.userId}/${reqId}`);
    const responseRef = ref(database, `responses/${this.userId}/${reqId}`);

    return new Promise<T>((resolve, reject) => {
      const timeout = setTimeout(() => {
        off(responseRef);
        reject(new Error(`Bridge request timed out for action '${action}'`));
      }, 15000);

      // Listen for response
      onValue(responseRef, (snapshot) => {
        const val = snapshot.val();
        if (val !== null && val !== undefined) {
          clearTimeout(timeout);
          off(responseRef);
          // Clean up response node
          remove(responseRef).catch(() => {});

          if (val.success === false) {
            reject(new Error(val.error || `Failed executing ${action}`));
          } else {
            resolve(val as T);
          }
        }
      });

      // Write request including signed Telegram initData
      set(requestRef, {
        action,
        payload,
        initData: this.initData,
        username: this.username,
        timestamp: Date.now(),
      }).catch((err) => {
        clearTimeout(timeout);
        off(responseRef);
        reject(err);
      });
    });
  }

  // --- Convenience Methods ---

  public async searchMedia(type: 'movie' | 'series', term: string): Promise<SearchResult[]> {
    const action = type === 'movie' ? 'search_movie' : 'search_series';
    const res = await this.sendCommand<{ results: SearchResult[] }>(action, { term });
    return res.results || [];
  }

  public async getDiscoverMovies(limit: number = 24): Promise<SearchResult[]> {
    const CACHE_KEY = 'addarr_discover_movies_cache_v1';
    const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

    try {
      const cachedStr = localStorage.getItem(CACHE_KEY);
      if (cachedStr) {
        const cached = JSON.parse(cachedStr);
        if (cached && cached.timestamp && Date.now() - cached.timestamp < CACHE_TTL_MS && Array.isArray(cached.items)) {
          return cached.items.slice(0, limit);
        }
      }
    } catch (e) {
      console.warn('Could not read discover movies from local cache:', e);
    }

    const res = await this.sendCommand<{ results: SearchResult[] }>('get_discover_movies', { limit });
    const results = res.results || [];

    try {
      localStorage.setItem(
        CACHE_KEY,
        JSON.stringify({
          timestamp: Date.now(),
          items: results,
        })
      );
    } catch (e) {
      console.warn('Could not write discover movies to local cache:', e);
    }

    return results;
  }

  public async addMovie(tmdbId: number, path: string, qualityProfileId: number): Promise<boolean> {
    const res = await this.sendCommand<{ success: boolean }>('add_movie', {
      tmdbId,
      path,
      qualityProfileId,
    });
    if (res.success) {
      // Evict added movie from discover cache
      try {
        const CACHE_KEY = 'addarr_discover_movies_cache_v1';
        const cachedStr = localStorage.getItem(CACHE_KEY);
        if (cachedStr) {
          const cached = JSON.parse(cachedStr);
          if (cached && Array.isArray(cached.items)) {
            cached.items = cached.items.filter((item: SearchResult) => item.id !== tmdbId);
            localStorage.setItem(CACHE_KEY, JSON.stringify(cached));
          }
        }
      } catch (e) {
        console.warn('Could not evict movie from local discover cache:', e);
      }
    }
    return res.success;
  }

  public async addSeries(tvdbId: number, path: string, qualityProfileId: number, seasonsSelected?: any): Promise<boolean> {
    const res = await this.sendCommand<{ success: boolean }>('add_series', {
      tvdbId,
      path,
      qualityProfileId,
      seasonsSelected,
    });
    return res.success;
  }

  public async getLibrary(type: 'movie' | 'series'): Promise<LibraryItem[]> {
    const action = type === 'movie' ? 'get_library_movies' : 'get_library_series';
    const res = await this.sendCommand<{ items: LibraryItem[] }>(action);
    return res.items || [];
  }

  public async getCalendar(type: MediaType, days: number = 60, limit: number = 20): Promise<CalendarItem[]> {
    const action = type === 'movie' ? 'get_calendar_movies' : 'get_calendar_series';
    const res = await this.sendCommand<{ items: CalendarItem[] }>(action, { days, limit });
    return res.items || [];
  }

  public async updateMovie(movieId: number, qualityProfileId?: number, monitored?: boolean): Promise<any> {
    return this.sendCommand('update_movie', { movieId, qualityProfileId, monitored });
  }

  public async updateSeries(
    seriesId: number,
    qualityProfileId?: number,
    monitored?: boolean,
    seasons?: Array<{ seasonNumber: number; monitored: boolean }>
  ): Promise<any> {
    return this.sendCommand('update_series', { seriesId, qualityProfileId, monitored, seasons });
  }

  public async deleteMedia(type: 'movie' | 'series', id: number): Promise<boolean> {
    const action = type === 'movie' ? 'delete_movie' : 'delete_series';
    const payload = type === 'movie' ? { tmdbId: id } : { tvdbId: id };
    const res = await this.sendCommand<{ success: boolean }>(action, payload);
    return res.success;
  }

  public async getConfigOptions(): Promise<AppConfigOptions> {
    return this.sendCommand<AppConfigOptions>('get_config_options');
  }
}

export const bridge = new BridgeService();
