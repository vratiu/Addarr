import React, { useState } from 'react';
import { X, Check, Folder, Sliders, Loader2, ExternalLink } from 'lucide-react';
import { SearchResult, MediaType, AppConfigOptions } from '../types';
import { bridge } from '../services/bridge';

interface QuickAddModalProps {
  item: SearchResult;
  mediaType: MediaType;
  configOptions: AppConfigOptions | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const QuickAddModal: React.FC<QuickAddModalProps> = ({
  item,
  mediaType,
  configOptions,
  onClose,
  onSuccess,
}) => {
  const options = mediaType === 'movie' ? configOptions?.radarr : configOptions?.sonarr;
  const rootFolders = options?.rootFolders || [];
  const qualityProfiles = options?.qualityProfiles || [];

  const [selectedFolder, setSelectedFolder] = useState<string>(
    rootFolders[0]?.path || ''
  );
  const [selectedProfile, setSelectedProfile] = useState<number>(
    qualityProfiles[0]?.id || 1
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const imdbUrl = item.imdbId
    ? `https://www.imdb.com/title/${item.imdbId}/`
    : item.title
    ? `https://www.imdb.com/find/?q=${encodeURIComponent(item.title + (item.year ? ' ' + item.year : ''))}`
    : null;

  const handleOpenImdb = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!imdbUrl) return;
    if (window.Telegram?.WebApp?.openLink) {
      window.Telegram.WebApp.openLink(imdbUrl);
    } else {
      window.open(imdbUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const handleAdd = async () => {
    setLoading(true);
    setError(null);
    try {
      if (mediaType === 'movie') {
        await bridge.addMovie(item.id, selectedFolder, selectedProfile);
      } else {
        await bridge.addSeries(item.id, selectedFolder, selectedProfile);
      }
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to add media');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/70 backdrop-blur-sm p-0 sm:p-4 animate-fade-in">
      <div className="w-full max-w-md bg-tg-secondary border border-gray-700 rounded-t-2xl sm:rounded-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700/50">
          <h2 className="font-semibold text-sm">Add to {mediaType === 'movie' ? 'Radarr' : 'Sonarr'}</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-tg-hint hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Media Preview */}
        <div className="p-4 flex space-x-3 bg-tg-bg/50">
          {item.poster ? (
            <img
              src={item.poster}
              alt={item.title}
              className="w-16 h-24 object-cover rounded-lg shadow border border-gray-800 flex-shrink-0"
            />
          ) : (
            <div className="w-16 h-24 bg-gray-800 rounded-lg flex items-center justify-center text-xs text-tg-hint flex-shrink-0">
              No Poster
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-1">
              <h3 className="font-bold text-base truncate flex-1">{item.title}</h3>
              {imdbUrl && (
                <button
                  type="button"
                  onClick={handleOpenImdb}
                  className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-[#f5c518] hover:bg-[#e2b616] text-black font-extrabold text-[11px] leading-tight transition shadow-sm flex-shrink-0 cursor-pointer active:scale-95"
                  title="View on IMDb"
                >
                  <span>IMDb</span>
                  <ExternalLink className="w-3 h-3" />
                </button>
              )}
            </div>
            <p className="text-xs text-tg-hint mt-0.5">{item.year || 'Unknown'}</p>
            {item.overview && (
              <p className="text-xs text-gray-400 mt-2 line-clamp-2">
                {item.overview}
              </p>
            )}
          </div>
        </div>

        {/* Configuration Options */}
        <div className="p-4 space-y-4">
          {/* Quality Profile */}
          <div>
            <label className="flex items-center text-xs font-medium text-tg-hint mb-1">
              <Sliders className="w-3.5 h-3.5 mr-1" />
              Quality Profile
            </label>
            <select
              value={selectedProfile}
              onChange={(e) => setSelectedProfile(Number(e.target.value))}
              className="w-full bg-tg-bg border border-gray-700 rounded-xl px-3 py-2 text-sm text-tg-text focus:outline-none focus:border-tg-button transition"
            >
              {qualityProfiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Root Folder */}
          <div>
            <label className="flex items-center text-xs font-medium text-tg-hint mb-1">
              <Folder className="w-3.5 h-3.5 mr-1" />
              Root Folder
            </label>
            <select
              value={selectedFolder}
              onChange={(e) => setSelectedFolder(e.target.value)}
              className="w-full bg-tg-bg border border-gray-700 rounded-xl px-3 py-2 text-sm text-tg-text focus:outline-none focus:border-tg-button transition truncate"
            >
              {rootFolders.map((f) => (
                <option key={f.id || f.path} value={f.path}>
                  {f.path}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="p-2.5 bg-red-950/40 border border-red-800/60 rounded-xl text-red-400 text-xs">
              {error}
            </div>
          )}

          {/* Action Button */}
          <button
            onClick={handleAdd}
            disabled={loading}
            className="w-full flex items-center justify-center space-x-2 bg-tg-button text-tg-buttonText font-semibold py-3 rounded-xl shadow-lg hover:opacity-95 active:scale-[0.98] transition disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Check className="w-5 h-5" />
                <span>Confirm & Add Now</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
