export type MediaType = 'movie' | 'series';

export interface SearchResult {
  id: number; // tmdbId or tvdbId
  title: string;
  year: number;
  overview?: string;
  poster?: string;
  seasonCount?: number;
}

export interface LibraryItem {
  id: number; // DB ID in Sonarr / Radarr
  tmdbId?: number;
  tvdbId?: number;
  title: string;
  year: number;
  poster?: string;
  qualityProfileId: number;
  monitored: boolean;
  status: string;
  hasFile?: boolean;
  sizeOnDisk?: number;
  seasonCount?: number;
  episodeCount?: number;
  episodeFileCount?: number;
  seasons?: Array<{ seasonNumber: number; monitored: boolean }>;
}

export interface QualityProfile {
  id: number;
  name: string;
}

export interface RootFolder {
  id: number;
  path: string;
  freeSpace?: number;
}

export interface AppConfigOptions {
  radarr: {
    qualityProfiles: QualityProfile[];
    rootFolders: RootFolder[];
  };
  sonarr: {
    qualityProfiles: QualityProfile[];
    rootFolders: RootFolder[];
  };
}
