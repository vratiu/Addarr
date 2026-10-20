export type MediaType = 'movie' | 'series';
export type TabType = 'search' | 'library' | 'calendar';

export interface CalendarItem {
  id: number;
  tmdbId?: number;
  tvdbId?: number;
  seriesId?: number;
  title: string;
  year?: number;
  poster?: string;
  releaseDate: string;
  releaseDateIso?: string;
  format?: string;
  seasonNumber?: number;
  episodeNumber?: number;
  endEpisodeNumber?: number;
  episodeCount?: number;
  episodeInfo?: string;
  episodeTitle?: string;
  hasFile?: boolean;
  monitored?: boolean;
}

export interface SearchResult {
  id: number; // tmdbId or tvdbId
  title: string;
  year: number;
  overview?: string;
  poster?: string;
  seasonCount?: number;
  imdbId?: string;
  inLibrary?: boolean;
  libraryId?: number; // DB ID in Radarr / Sonarr
  qualityProfileId?: number;
  monitored?: boolean;
  status?: string;
  hasFile?: boolean;
  sizeOnDisk?: number;
  episodeCount?: number;
  episodeFileCount?: number;
  seasons?: Array<{ seasonNumber: number; monitored: boolean }>;
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
