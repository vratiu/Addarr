import React, { useState, useEffect, useCallback } from 'react';
import { Search, Loader2, Plus, Film, Tv, Sparkles, CheckCircle, AlertCircle, EyeOff } from 'lucide-react';
import { SearchResult, LibraryItem, MediaType, AppConfigOptions } from '../types';
import { bridge } from '../services/bridge';
import { QuickAddModal } from './QuickAddModal';
import { PreferenceModal } from './PreferenceModal';

interface SearchTabProps {
  mediaType: MediaType;
  configOptions: AppConfigOptions | null;
}

export const SearchTab: React.FC<SearchTabProps> = ({ mediaType, configOptions }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [discoverSuggestions, setDiscoverSuggestions] = useState<SearchResult[]>([]);
  const [discoverLoading, setDiscoverLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<SearchResult | null>(null);
  const [editingLibraryItem, setEditingLibraryItem] = useState<LibraryItem | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const runSearch = useCallback(async (searchQuery: string, type: MediaType) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const data = await bridge.searchMedia(type, searchQuery.trim());
      setResults(data);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load Discover suggestions non-blockingly when landing on Movie search
  useEffect(() => {
    if (mediaType !== 'movie') {
      return;
    }

    let isMounted = true;
    const fetchSuggestions = async () => {
      // If we already loaded suggestions, don't trigger loader again
      if (discoverSuggestions.length === 0) {
        setDiscoverLoading(true);
      }
      try {
        const data = await bridge.getDiscoverMovies(24);
        if (isMounted) {
          setDiscoverSuggestions(data);
        }
      } catch (err) {
        console.warn('Could not fetch discover suggestions:', err);
      } finally {
        if (isMounted) {
          setDiscoverLoading(false);
        }
      }
    };

    fetchSuggestions();

    return () => {
      isMounted = false;
    };
  }, [mediaType]);

  // Debounced search trigger
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(() => {
      runSearch(query, mediaType);
    }, 450);

    return () => clearTimeout(timer);
  }, [query, mediaType, runSearch]);

  const handleItemClick = (item: SearchResult) => {
    if (item.inLibrary && item.libraryId) {
      const libItem: LibraryItem = {
        id: item.libraryId,
        tmdbId: mediaType === 'movie' ? item.id : undefined,
        tvdbId: mediaType === 'series' ? item.id : undefined,
        title: item.title,
        year: item.year,
        poster: item.poster,
        qualityProfileId: item.qualityProfileId || 1,
        monitored: item.monitored ?? true,
        status: item.status || 'released',
        hasFile: item.hasFile,
        sizeOnDisk: item.sizeOnDisk,
        seasonCount: item.seasonCount,
        episodeCount: item.episodeCount,
        episodeFileCount: item.episodeFileCount,
        seasons: item.seasons,
      };
      setEditingLibraryItem(libItem);
    } else {
      setSelectedItem(item);
    }
  };

  const handleAddedSuccess = () => {
    const title = selectedItem?.title;
    const addedId = selectedItem?.id;

    // Remove added movie from discover suggestions grid if present
    if (addedId) {
      setDiscoverSuggestions((prev) => prev.filter((item) => item.id !== addedId));
    }

    setSelectedItem(null);
    setSuccessNotice(`Successfully added "${title}"!`);
    setTimeout(() => setSuccessNotice(null), 3500);

    // Refresh search results to reflect the newly added library status
    if (query.trim()) {
      runSearch(query, mediaType);
    }
  };

  const handleUpdatedSuccess = () => {
    const title = editingLibraryItem?.title;
    setEditingLibraryItem(null);
    setSuccessNotice(`Successfully updated "${title}"!`);
    setTimeout(() => setSuccessNotice(null), 3500);

    // Refresh search results to reflect preferences or removal
    if (query.trim()) {
      runSearch(query, mediaType);
    }
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

      {/* When query is empty: show Discover Suggestions on Movie tab, or default prompt */}
      {!query.trim() && (
        <>
          {mediaType === 'movie' ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-tg-text">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <span>Suggestions from Radarr Explore</span>
                </div>
                {discoverLoading && (
                  <div className="flex items-center space-x-1 text-[11px] text-tg-hint">
                    <Loader2 className="w-3 h-3 animate-spin text-tg-link" />
                    <span>Loading...</span>
                  </div>
                )}
              </div>

              {discoverSuggestions.length > 0 ? (
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                  {discoverSuggestions.map((item) => (
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
                            <Film className="w-6 h-6 mb-1" />
                            <span className="text-[10px] line-clamp-2">{item.title}</span>
                          </div>
                        )}

                        {/* Quick Add Button Overlay */}
                        <div className="absolute top-1.5 right-1.5">
                          <div className="p-1 rounded-full bg-tg-button/90 text-white shadow-md hover:scale-110 active:scale-95 transition">
                            <Plus className="w-3.5 h-3.5" />
                          </div>
                        </div>
                      </div>

                      {/* Title & Info */}
                      <div className="p-2 bg-tg-secondary">
                        <h4 className="font-semibold text-xs leading-snug line-clamp-1 group-hover:text-tg-link transition">
                          {item.title}
                        </h4>
                        <div className="text-[10px] text-tg-hint mt-0.5">
                          <span>{item.year || 'Unknown'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                !discoverLoading && (
                  <div className="text-center py-12 text-tg-hint text-sm">
                    Type a title above to search Radarr.
                  </div>
                )
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-tg-hint text-sm">
              Type a title above to search Sonarr.
            </div>
          )}
        </>
      )}

      {/* Results List for Active Search */}
      {query.trim() && (
        <div className="space-y-3">
          {results.map((item) => {
            const isDownloaded = item.hasFile || (item.episodeFileCount !== undefined && item.episodeFileCount > 0);
            const isMonitored = item.monitored;

            return (
              <div
                key={item.id}
                onClick={() => handleItemClick(item)}
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
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-sm leading-snug line-clamp-1">{item.title}</h4>
                    {item.inLibrary && (
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${
                          isDownloaded
                            ? 'bg-green-950/80 text-green-400 border border-green-800/60'
                            : isMonitored
                            ? 'bg-yellow-950/80 text-yellow-400 border border-yellow-800/60'
                            : 'bg-gray-800/80 text-gray-400 border border-gray-700/60'
                        }`}
                      >
                        {isDownloaded ? 'Downloaded' : isMonitored ? 'Monitored' : 'Unmonitored'}
                      </span>
                    )}
                  </div>

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

                {item.inLibrary ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleItemClick(item);
                    }}
                    title="Manage in Library"
                    className={`p-2 rounded-xl transition flex-shrink-0 ${
                      isDownloaded
                        ? 'bg-green-950/80 border border-green-500/70 text-green-400 hover:bg-green-900/80'
                        : isMonitored
                        ? 'bg-yellow-950/80 border border-yellow-500/70 text-yellow-400 hover:bg-yellow-900/80'
                        : 'bg-gray-800/80 border border-gray-600/70 text-gray-400 hover:bg-gray-700/80'
                    }`}
                  >
                    {isDownloaded ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : isMonitored ? (
                      <AlertCircle className="w-5 h-5" />
                    ) : (
                      <EyeOff className="w-5 h-5" />
                    )}
                  </button>
                ) : (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleItemClick(item);
                    }}
                    title={`Add to ${mediaType === 'movie' ? 'Radarr' : 'Sonarr'}`}
                    className="p-2 rounded-xl bg-tg-button/20 text-tg-link hover:bg-tg-button hover:text-white transition flex-shrink-0"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                )}
              </div>
            );
          })}

          {!loading && results.length === 0 && (
            <div className="text-center py-12 text-tg-hint text-sm">
              No matching titles found for "{query}".
            </div>
          )}
        </div>
      )}

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

      {/* Preference Modal for Existing Library Items */}
      {editingLibraryItem && (
        <PreferenceModal
          item={editingLibraryItem}
          mediaType={mediaType}
          configOptions={configOptions}
          onClose={() => setEditingLibraryItem(null)}
          onUpdated={handleUpdatedSuccess}
        />
      )}
    </div>
  );
};
