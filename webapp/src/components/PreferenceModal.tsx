import React, { useState } from 'react';
import { X, Check, Sliders, Eye, Trash2, Loader2, CheckSquare, Square } from 'lucide-react';
import { LibraryItem, MediaType, AppConfigOptions } from '../types';
import { bridge } from '../services/bridge';

interface PreferenceModalProps {
  item: LibraryItem;
  mediaType: MediaType;
  configOptions: AppConfigOptions | null;
  onClose: () => void;
  onUpdated: () => void;
}

export const PreferenceModal: React.FC<PreferenceModalProps> = ({
  item,
  mediaType,
  configOptions,
  onClose,
  onUpdated,
}) => {
  const options = mediaType === 'movie' ? configOptions?.radarr : configOptions?.sonarr;
  const qualityProfiles = options?.qualityProfiles || [];

  const [selectedProfile, setSelectedProfile] = useState<number>(item.qualityProfileId || 1);
  const [monitored, setMonitored] = useState<boolean>(item.monitored ?? true);
  const [seasons, setSeasons] = useState<Array<{ seasonNumber: number; monitored: boolean }>>(
    item.seasons || []
  );
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleSeason = (seasonNumber: number) => {
    setSeasons((prev) =>
      prev.map((s) => (s.seasonNumber === seasonNumber ? { ...s, monitored: !s.monitored } : s))
    );
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    try {
      if (mediaType === 'movie') {
        await bridge.updateMovie(item.id, selectedProfile, monitored);
      } else {
        await bridge.updateSeries(item.id, selectedProfile, monitored, seasons);
      }
      onUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed to update preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete "${item.title}" from ${mediaType === 'movie' ? 'Radarr' : 'Sonarr'}?`)) {
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      const idToDelete = mediaType === 'movie' ? item.tmdbId || item.id : item.tvdbId || item.id;
      await bridge.deleteMedia(mediaType, idToDelete);
      onUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed to delete title');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/70 backdrop-blur-sm p-0 sm:p-4 animate-fade-in">
      <div className="w-full max-w-md bg-tg-secondary border border-gray-700 rounded-t-2xl sm:rounded-2xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700/50 flex-shrink-0">
          <h2 className="font-semibold text-sm">Manage {mediaType === 'movie' ? 'Movie' : 'Series'}</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-tg-hint hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Media Info */}
        <div className="p-4 flex space-x-3 bg-tg-bg/50 border-b border-gray-700/30 flex-shrink-0">
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
            <h3 className="font-bold text-base truncate">{item.title}</h3>
            <p className="text-xs text-tg-hint mt-0.5">{item.year || 'Unknown'}</p>
            <div className="flex items-center space-x-2 mt-2">
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                  item.hasFile || item.status === 'released' || item.status === 'ended'
                    ? 'bg-green-950/80 text-green-400 border border-green-800/60'
                    : 'bg-yellow-950/80 text-yellow-400 border border-yellow-800/60'
                }`}
              >
                {item.hasFile ? 'Downloaded' : item.status}
              </span>
            </div>
          </div>
        </div>

        {/* Scrollable Configuration */}
        <div className="p-4 space-y-4 overflow-y-auto flex-1">
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

          {/* Monitoring Toggle */}
          <div className="flex items-center justify-between p-3 bg-tg-bg border border-gray-700/60 rounded-xl">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-tg-link" />
              <div>
                <p className="text-sm font-medium">Monitored</p>
                <p className="text-[11px] text-tg-hint">Search for future releases</p>
              </div>
            </div>
            <button
              onClick={() => setMonitored(!monitored)}
              className={`w-12 h-6 flex items-center rounded-full p-1 transition duration-200 ${
                monitored ? 'bg-tg-button justify-end' : 'bg-gray-700 justify-start'
              }`}
            >
              <div className="w-4 h-4 rounded-full bg-white shadow-md"></div>
            </button>
          </div>

          {/* Granular Season Monitoring (Series only) */}
          {mediaType === 'series' && seasons.length > 0 && (
            <div>
              <p className="text-xs font-medium text-tg-hint mb-2">Monitored Seasons</p>
              <div className="grid grid-cols-2 gap-2">
                {seasons.map((s) => (
                  <button
                    key={s.seasonNumber}
                    onClick={() => toggleSeason(s.seasonNumber)}
                    className={`flex items-center space-x-2 p-2.5 rounded-xl border text-xs font-medium transition ${
                      s.monitored
                        ? 'bg-tg-button/20 border-tg-button text-white'
                        : 'bg-tg-bg border-gray-700/60 text-tg-hint'
                    }`}
                  >
                    {s.monitored ? (
                      <CheckSquare className="w-4 h-4 text-tg-link flex-shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-gray-500 flex-shrink-0" />
                    )}
                    <span>{s.seasonNumber === 0 ? 'Specials' : `Season ${s.seasonNumber}`}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="p-2.5 bg-red-950/40 border border-red-800/60 rounded-xl text-red-400 text-xs">
              {error}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-gray-700/50 bg-tg-secondary space-y-2 flex-shrink-0">
          <button
            onClick={handleSave}
            disabled={loading || deleting}
            className="w-full flex items-center justify-center space-x-2 bg-tg-button text-tg-buttonText font-semibold py-3 rounded-xl shadow-lg hover:opacity-95 active:scale-[0.98] transition disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Check className="w-5 h-5" />
                <span>Save Changes</span>
              </>
            )}
          </button>

          <button
            onClick={handleDelete}
            disabled={loading || deleting}
            className="w-full flex items-center justify-center space-x-2 bg-red-950/30 border border-red-800/50 text-red-400 font-medium py-2.5 rounded-xl hover:bg-red-950/60 active:scale-[0.98] transition disabled:opacity-50 text-xs"
          >
            {deleting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Trash2 className="w-4 h-4" />
                <span>Remove from {mediaType === 'movie' ? 'Radarr' : 'Sonarr'}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
