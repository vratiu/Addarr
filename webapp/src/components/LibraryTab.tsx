import React, { useState, useEffect, useMemo } from 'react';
import { Search, RefreshCw, Loader2, Filter, Film, Tv, CheckCircle, AlertCircle } from 'lucide-react';
import { LibraryItem, MediaType, AppConfigOptions } from '../types';
import { bridge } from '../services/bridge';
import { PreferenceModal } from './PreferenceModal';

interface LibraryTabProps {
  mediaType: MediaType;
  configOptions: AppConfigOptions | null;
}

type FilterType = 'all' | 'downloaded' | 'missing' | 'unmonitored';
type SortType = 'title' | 'year';

export const LibraryTab: React.FC<LibraryTabProps> = ({ mediaType, configOptions }) => {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [sortBy, setSortBy] = useState<SortType>('title');
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedItem, setSelectedItem] = useState<LibraryItem | null>(null);

  const fetchLibrary = async () => {
    setLoading(true);
    try {
      const data = await bridge.getLibrary(mediaType);
      setItems(data);
    } catch (err) {
      console.error('Failed to load library:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLibrary();
  }, [mediaType]);

  const filteredItems = useMemo(() => {
    let result = items;

    // Search query
    if (searchFilter.trim()) {
      const q = searchFilter.toLowerCase();
      result = result.filter((i) => i.title.toLowerCase().includes(q));
    }

    // Status Filter
    if (filterType === 'downloaded') {
      result = result.filter((i) => i.hasFile || (i.episodeFileCount && i.episodeFileCount > 0));
    } else if (filterType === 'missing') {
      result = result.filter(
        (i) => i.monitored && (!i.hasFile && (i.episodeFileCount === undefined || i.episodeFileCount === 0))
      );
    } else if (filterType === 'unmonitored') {
      result = result.filter((i) => !i.monitored);
    }

    // Sorting
    return [...result].sort((a, b) => {
      if (sortBy === 'year') {
        return (b.year || 0) - (a.year || 0);
      }
      return a.title.localeCompare(b.title);
    });
  }, [items, searchFilter, filterType, sortBy]);

  return (
    <div className="p-4 space-y-4">
      {/* Search & Actions Bar */}
      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-tg-hint" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder={`Filter ${items.length} titles...`}
            className="w-full bg-tg-secondary border border-gray-700/70 rounded-xl pl-10 pr-4 py-2.5 text-sm text-tg-text placeholder-tg-hint focus:outline-none focus:border-tg-button transition shadow-inner"
          />
        </div>
        <button
          onClick={fetchLibrary}
          disabled={loading}
          className="p-2.5 bg-tg-secondary border border-gray-700/70 rounded-xl text-tg-hint hover:text-white transition disabled:opacity-50"
          title="Refresh Library"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-tg-link' : ''}`} />
        </button>
      </div>

      {/* Filter & Sort Pills */}
      <div className="flex items-center justify-between text-xs overflow-x-auto pb-1 space-x-2 scrollbar-none">
        <div className="flex items-center space-x-1.5 flex-shrink-0">
          {(['all', 'downloaded', 'missing', 'unmonitored'] as FilterType[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilterType(f)}
              className={`capitalize px-2.5 py-1 rounded-lg font-medium transition ${
                filterType === f
                  ? 'bg-tg-button text-white shadow'
                  : 'bg-tg-secondary text-tg-hint hover:text-tg-text border border-gray-800'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortType)}
          className="bg-tg-secondary border border-gray-700 text-tg-hint text-xs rounded-lg px-2 py-1 focus:outline-none"
        >
          <option value="title">A-Z</option>
          <option value="year">Year</option>
        </select>
      </div>

      {/* Grid of Posters */}
      {loading && items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-2 text-tg-hint">
          <Loader2 className="w-8 h-8 animate-spin text-tg-link" />
          <p className="text-sm">Loading library...</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              onClick={() => setSelectedItem(item)}
              className="group relative flex flex-col bg-tg-secondary rounded-xl overflow-hidden border border-gray-700/50 hover:border-tg-button/70 cursor-pointer transition shadow hover:shadow-lg active:scale-95"
            >
              {/* Poster Container */}
              <div className="relative aspect-[2/3] bg-tg-bg overflow-hidden">
                {item.poster ? (
                  <img
                    src={item.poster}
                    alt={item.title}
                    loading="lazy"
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-tg-hint p-2 text-center">
                    {mediaType === 'movie' ? <Film className="w-6 h-6 mb-1" /> : <Tv className="w-6 h-6 mb-1" />}
                    <span className="text-[10px] line-clamp-2">{item.title}</span>
                  </div>
                )}

                {/* Status Badges */}
                <div className="absolute top-1 right-1 flex flex-col space-y-1">
                  {item.hasFile || (item.episodeFileCount && item.episodeFileCount > 0) ? (
                    <div className="p-0.5 rounded-full bg-green-950/90 border border-green-500/80 shadow">
                      <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                    </div>
                  ) : item.monitored ? (
                    <div className="p-0.5 rounded-full bg-yellow-950/90 border border-yellow-500/80 shadow">
                      <AlertCircle className="w-3.5 h-3.5 text-yellow-400" />
                    </div>
                  ) : null}
                </div>
              </div>

              {/* Title & Info */}
              <div className="p-2 bg-tg-secondary">
                <h4 className="font-semibold text-xs leading-snug line-clamp-1 group-hover:text-tg-link transition">
                  {item.title}
                </h4>
                <div className="flex items-center justify-between text-[10px] text-tg-hint mt-0.5">
                  <span>{item.year || 'Unknown'}</span>
                  {item.seasonCount !== undefined && (
                    <span>{item.seasonCount}S</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filteredItems.length === 0 && (
        <div className="text-center py-16 text-tg-hint text-sm">
          No titles found matching the selected filter.
        </div>
      )}

      {/* Edit Preferences Modal */}
      {selectedItem && (
        <PreferenceModal
          item={selectedItem}
          mediaType={mediaType}
          configOptions={configOptions}
          onClose={() => setSelectedItem(null)}
          onUpdated={() => {
            setSelectedItem(null);
            fetchLibrary();
          }}
        />
      )}
    </div>
  );
};
