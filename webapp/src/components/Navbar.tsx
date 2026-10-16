import React from 'react';
import { Film, Tv, Search, Library } from 'lucide-react';
import { MediaType } from '../types';

interface NavbarProps {
  activeTab: 'search' | 'library';
  setActiveTab: (tab: 'search' | 'library') => void;
  mediaType: MediaType;
  setMediaType: (type: MediaType) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  mediaType,
  setMediaType,
}) => {
  return (
    <header className="sticky top-0 z-30 bg-tg-secondary/95 backdrop-blur border-b border-gray-700/50 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* App Title */}
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-tg-button flex items-center justify-center font-bold text-white shadow">
            A
          </div>
          <div>
            <h1 className="font-bold text-base leading-tight">Addarr</h1>
            <p className="text-xs text-tg-hint">Media Manager</p>
          </div>
        </div>

        {/* Media Type Switcher: Movies / Series */}
        <div className="flex items-center bg-tg-bg rounded-lg p-1 border border-gray-700/50">
          <button
            onClick={() => setMediaType('movie')}
            className={`flex items-center space-x-1 px-3 py-1 text-xs font-medium rounded-md transition ${
              mediaType === 'movie'
                ? 'bg-tg-button text-white shadow'
                : 'text-tg-hint hover:text-tg-text'
            }`}
          >
            <Film className="w-3.5 h-3.5" />
            <span>Movies</span>
          </button>
          <button
            onClick={() => setMediaType('series')}
            className={`flex items-center space-x-1 px-3 py-1 text-xs font-medium rounded-md transition ${
              mediaType === 'series'
                ? 'bg-tg-button text-white shadow'
                : 'text-tg-hint hover:text-tg-text'
            }`}
          >
            <Tv className="w-3.5 h-3.5" />
            <span>Series</span>
          </button>
        </div>
      </div>

      {/* Tabs: Search & Add / Library */}
      <div className="flex border-b border-gray-700/50 mt-3 -mx-4 px-4 space-x-6 text-sm">
        <button
          onClick={() => setActiveTab('search')}
          className={`flex items-center space-x-1.5 pb-2 font-medium border-b-2 transition ${
            activeTab === 'search'
              ? 'border-tg-button text-tg-link'
              : 'border-transparent text-tg-hint hover:text-tg-text'
          }`}
        >
          <Search className="w-4 h-4" />
          <span>Search & Add</span>
        </button>
        <button
          onClick={() => setActiveTab('library')}
          className={`flex items-center space-x-1.5 pb-2 font-medium border-b-2 transition ${
            activeTab === 'library'
              ? 'border-tg-button text-tg-link'
              : 'border-transparent text-tg-hint hover:text-tg-text'
          }`}
        >
          <Library className="w-4 h-4" />
          <span>My Library</span>
        </button>
      </div>
    </header>
  );
};
