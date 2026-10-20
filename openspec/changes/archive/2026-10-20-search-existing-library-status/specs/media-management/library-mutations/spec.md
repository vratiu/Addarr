# Spec Delta

## MODIFIED Requirements

### Requirement: Query Enriched Library Data
The system SHALL retrieve existing media items from Sonarr and Radarr including poster art, quality profile, disk status, and monitoring state, and SHALL enrich search lookup results with these library fields whenever a searched movie or series already exists in the local library.

#### Scenario: Retrieve movies list
- **WHEN** the library query for movies is executed
- **THEN** the system returns all movies with ID, title, year, poster URL, quality profile ID, monitored status, and download status

#### Scenario: Enrich movie search results with library status
- **WHEN** a movie search lookup returns an item that already exists in Radarr (`id > 0`)
- **THEN** the formatted search result includes `inLibrary: true`, `libraryId` (Radarr database ID), `qualityProfileId`, `monitored`, `status`, `hasFile`, and `sizeOnDisk` while keeping `id` as `tmdbId`

#### Scenario: Enrich series search results with library status
- **WHEN** a series search lookup returns an item that already exists in Sonarr (`id > 0`)
- **THEN** the formatted search result includes `inLibrary: true`, `libraryId` (Sonarr database ID), `qualityProfileId`, `monitored`, `status`, `episodeCount`, `episodeFileCount`, and `seasons` while keeping `id` as `tvdbId`
