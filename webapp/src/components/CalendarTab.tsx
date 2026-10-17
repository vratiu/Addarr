import React, { useState, useEffect } from 'react';
import { Calendar, RefreshCw, Loader2, Film, Tv, CheckCircle, Clock } from 'lucide-react';
import { CalendarItem, MediaType } from '../types';
import { bridge } from '../services/bridge';

interface CalendarTabProps {
  mediaType: MediaType;
}

export function formatReleaseDate(dateStr: string): { formattedDate: string; relativeText?: string } {
  if (!dateStr) return { formattedDate: 'Unknown date' };

  const [year, month, day] = dateStr.slice(0, 10).split('-').map(Number);
  if (!year || !month || !day) return { formattedDate: dateStr };

  const releaseDate = new Date(year, month - 1, day);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const formattedDate = releaseDate.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: releaseDate.getFullYear() !== today.getFullYear() ? 'numeric' : undefined,
  });

  const diffTime = releaseDate.getTime() - today.getTime();
  const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

  let relativeText: string | undefined;
  if (diffDays >= 0 && diffDays < 14) {
    if (diffDays === 0) {
      relativeText = 'today';
    } else if (diffDays === 1) {
      relativeText = 'tomorrow';
    } else {
      relativeText = `in ${diffDays} days`;
    }
  }

  return { formattedDate, relativeText };
}

export const CalendarTab: React.FC<CalendarTabProps> = ({ mediaType }) => {
  const [items, setItems] = useState<CalendarItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCalendar = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await bridge.getCalendar(mediaType, 60, 20);
      setItems(data);
    } catch (err: any) {
      console.error('Failed to load calendar:', err);
      setError(err?.message || 'Failed to load upcoming releases');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalendar();
  }, [mediaType]);

  return (
    <div className="p-4 space-y-4">
      {/* Header Bar */}
      <div className="flex items-center justify-between pb-1">
        <div className="flex items-center space-x-2">
          <Calendar className="w-5 h-5 text-tg-link" />
          <h2 className="font-semibold text-sm">
            Upcoming {mediaType === 'movie' ? 'Digital Releases' : 'Episodes'}
          </h2>
          <span className="text-xs text-tg-hint">
            ({items.length} {items.length === 1 ? 'entry' : 'entries'})
          </span>
        </div>

        <button
          onClick={fetchCalendar}
          disabled={loading}
          className="p-2 bg-tg-secondary border border-gray-700/70 rounded-xl text-tg-hint hover:text-white transition disabled:opacity-50"
          title="Refresh Calendar"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-tg-link' : ''}`} />
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-xl text-red-300 text-xs">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-2 text-tg-hint">
          <Loader2 className="w-8 h-8 animate-spin text-tg-link" />
          <p className="text-sm">Loading upcoming {mediaType === 'movie' ? 'movies' : 'episodes'}...</p>
        </div>
      ) : (
        /* Calendar List */
        <div className="space-y-3">
          {items.map((item) => {
            const { formattedDate, relativeText } = formatReleaseDate(item.releaseDate);

            return (
              <div
                key={`${item.id}-${item.releaseDate}`}
                className="flex items-center space-x-3 p-3 bg-tg-secondary/70 hover:bg-tg-secondary border border-gray-700/50 hover:border-tg-button/50 rounded-xl transition shadow"
              >
                {/* Poster Thumbnail */}
                {item.poster ? (
                  <img
                    src={item.poster}
                    alt={item.title}
                    loading="lazy"
                    className="w-14 h-20 object-cover rounded-lg border border-gray-800 flex-shrink-0"
                  />
                ) : (
                  <div className="w-14 h-20 bg-tg-bg rounded-lg flex items-center justify-center text-xs text-tg-hint flex-shrink-0">
                    {mediaType === 'movie' ? <Film className="w-5 h-5" /> : <Tv className="w-5 h-5" />}
                  </div>
                )}

                {/* Content Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-sm leading-snug line-clamp-1">
                      {item.title}
                    </h4>
                    {item.hasFile && (
                      <span
                        className="flex items-center space-x-1 text-[10px] text-green-400 font-medium ml-2 flex-shrink-0"
                        title="Downloaded"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Downloaded</span>
                      </span>
                    )}
                  </div>

                  {/* Metadata / Episode info */}
                  {mediaType === 'series' ? (
                    <div className="text-xs text-tg-hint mt-1 flex items-center space-x-1.5">
                      <span className="font-medium text-tg-link">
                        {item.episodeInfo || `S${item.seasonNumber}E${item.episodeNumber}`}
                      </span>
                      {item.episodeTitle && item.episodeCount === 1 && (
                        <>
                          <span>•</span>
                          <span className="truncate">{item.episodeTitle}</span>
                        </>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs text-tg-hint mt-1 flex items-center space-x-1.5">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-800 text-gray-300">
                        Digital Format
                      </span>
                      {item.year && <span>({item.year})</span>}
                    </div>
                  )}

                  {/* Date row */}
                  <div className="flex items-center space-x-2 text-xs text-gray-400 mt-2">
                    <Clock className="w-3.5 h-3.5 text-tg-hint flex-shrink-0" />
                    <span className="font-medium text-tg-text">{formattedDate}</span>
                    {relativeText && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-tg-button/20 text-tg-link">
                        ({relativeText})
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty state */}
      {!loading && items.length === 0 && !error && (
        <div className="text-center py-16 text-tg-hint text-sm space-y-1">
          <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="font-medium">No upcoming releases scheduled</p>
          <p className="text-xs text-gray-500">
            No monitored {mediaType === 'movie' ? 'movie digital releases' : 'series episodes'} found in the next 60 days.
          </p>
        </div>
      )}
    </div>
  );
};

export default CalendarTab;
