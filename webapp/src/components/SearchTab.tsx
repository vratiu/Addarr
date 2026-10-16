import React, { useState, useEffect } from 'react';
import { Search, Loader2, Plus, Film, Tv } from 'lucide-react';
import { SearchResult, MediaType, AppConfigOptions } from '../types';
import { bridge } from '../services/bridge';
import { QuickAddModal } from './QuickAddModal';

interface SearchTabProps {
  mediaType: MediaType;
  configOptions: AppConfigOptions | null;
}

export const SearchTab: React.FC<SearchTabProps> = ({ mediaType, configOptions }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<SearchResult | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  // Debounced search trigger
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await bridge.searchMedia(mediaType, query.trim());
        setResults(data);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setLoading(false);
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [query, mediaType]);

  const handleAddedSuccess = () => {
    const title = selectedItem?.title;
    setSelectedItem(null);
    setSuccessNotice(`Successfully added "${title}"!`);
    setTimeout(() => setSuccessNotice(null), 3500);
  };

  return (
    <div className="p-4 space-y-4">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-tg-hint" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={`Search ${mediaType === 'movie' ? 'movies' : 'series'}...`}
          className="w-full bg-tg-secondary border border-gray-700/70 rounded-xl pl-10 pr-10 py-2.5 text-sm text-tg-text placeholder-tg-hint focus:outline-none focus:border-tg-button transition shadow-inner"
        />
        {loading && (
          <Loader2 className="absolute right-3.5 top-3.5 w-4 h-4 text-tg-link animate-spin" />
        )}
      </div>

      {/* Success Banner */}
      {successNotice && (
        <div className="p-3 bg-green-950/40 border border-green-800/60 rounded-xl text-green-400 text-xs font-medium animate-fade-in flex items-center justify-between">
          <span>{successNotice}</span>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-3">
        {results.map((item) => (
          <div
            key={item.id}
            onClick={() => setSelectedItem(item)}
            className="flex items-center space-x-3 p-3 bg-tg-secondary/70 hover:bg-tg-secondary border border-gray-700/50 hover:border-tg-button/50 rounded-xl cursor-pointer transition active:scale-[0.99] shadow"
          >
            {item.poster ? (
              <img
                src={item.poster}
                alt={item.title}
                className="w-14 h-20 object-cover rounded-lg border border-gray-800 flex-shrink-0"
              />
            ) : (
              <div className="w-14 h-20 bg-tg-bg rounded-lg flex items-center justify-center text-xs text-tg-hint flex-shrink-0">
                {mediaType === 'movie' ? <Film className="w-5 h-5" /> : <Tv className="w-5 h-5" />}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-sm leading-snug line-clamp-1">{item.title}</h4>
              <div className="flex items-center space-x-2 text-xs text-tg-hint mt-1">
                <span>{item.year || 'Unknown'}</span>
                {item.seasonCount !== undefined && (
                  <>
                    <span>•</span>
                    <span>{item.seasonCount} Season{item.seasonCount !== 1 ? 's' : ''}</span>
                  </>
                )}
              </div>
              {item.overview && (
                <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                  {item.overview}
                </p>
              )}
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedItem(item);
              }}
              className="p-2 rounded-xl bg-tg-button/20 text-tg-link hover:bg-tg-button hover:text-white transition flex-shrink-0"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
        ))}

        {!loading && query.trim() && results.length === 0 && (
          <div className="text-center py-12 text-tg-hint text-sm">
            No matching titles found for "{query}".
          </div>
        )}

        {!query.trim() && (
          <div className="text-center py-12 text-tg-hint text-sm">
            Type a title above to search {mediaType === 'movie' ? 'Radarr' : 'Sonarr'}.
          </div>
        )}
      </div>

      {/* Quick Add Modal */}
      {selectedItem && (
        <QuickAddModal
          item={selectedItem}
          mediaType={mediaType}
          configOptions={configOptions}
          onClose={() => setSelectedItem(null)}
          onSuccess={handleAddedSuccess}
        />
      )}
    </div>
  );
};
