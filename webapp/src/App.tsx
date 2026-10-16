import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { SearchTab } from './components/SearchTab';
import { LibraryTab } from './components/LibraryTab';
import { MediaType, AppConfigOptions } from './types';
import { bridge } from './services/bridge';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'search' | 'library'>('search');
  const [mediaType, setMediaType] = useState<MediaType>('movie');
  const [configOptions, setConfigOptions] = useState<AppConfigOptions | null>(null);
  const [bridgeConnected, setBridgeConnected] = useState<boolean>(true);

  useEffect(() => {
    // Notify Telegram that WebApp is ready
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }

    // Load available quality profiles and root folders from Addarr
    const loadConfig = async () => {
      try {
        const opts = await bridge.getConfigOptions();
        setConfigOptions(opts);
        setBridgeConnected(true);
      } catch (err) {
        console.warn('Could not load remote config options (Addarr bridge may be connecting):', err);
        setBridgeConnected(false);
      }
    };

    loadConfig();
  }, []);

  return (
    <div className="min-h-screen bg-tg-bg text-tg-text pb-10">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        mediaType={mediaType}
        setMediaType={setMediaType}
      />

      <main className="max-w-2xl mx-auto">
        {!bridgeConnected && (
          <div className="m-4 p-3 bg-yellow-950/40 border border-yellow-800/60 rounded-xl text-yellow-300 text-xs">
            Connecting to Addarr homelab bridge... Requests will queue until connected.
          </div>
        )}

        {activeTab === 'search' ? (
          <SearchTab mediaType={mediaType} configOptions={configOptions} />
        ) : (
          <LibraryTab mediaType={mediaType} configOptions={configOptions} />
        )}
      </main>
    </div>
  );
};

export default App;
