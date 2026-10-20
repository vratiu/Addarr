# Spec Delta

## MODIFIED Requirements

### Requirement: Search Media with Visual Results
The client SHALL allow users to search for movies or series, view results with poster art, year, and overview in horizontal list rows, and visually distinguish items already present in the library by rendering their library status icon (`CheckCircle` for downloaded, `AlertCircle` for monitored/missing, or `EyeOff` for unmonitored) instead of the `+` add button.

#### Scenario: Search for media title
- **WHEN** user enters a title into the search input
- **THEN** the client displays matching titles with poster art, release year, overview summary, and a `+` action button for unadded titles or a library status indicator for existing titles

#### Scenario: Search for media title already in library
- **WHEN** user enters a title into the search input and a matching movie or series already exists in Radarr or Sonarr
- **THEN** the client displays the horizontal result row with its library status badge (`Downloaded`, `Monitored`, or `Unmonitored`) and the corresponding library status icon (`CheckCircle`, `AlertCircle`, or `EyeOff`) in place of the `+` button

#### Scenario: Refresh search row state after adding media
- **WHEN** user adds a movie or series from the search results via the quick-add modal
- **THEN** the client refreshes the search results so the newly added item immediately transitions from the `+` button to its library status indicator

### Requirement: Edit Media Preferences
The client SHALL allow users to modify quality profiles, monitoring status, and season monitoring for existing library items from both the library view and search results.

#### Scenario: Change quality profile of an existing title
- **WHEN** user selects a new quality profile for an existing movie or series and confirms
- **THEN** the client submits the update command and reflects the updated profile immediately

#### Scenario: Open and edit preferences for an existing title from search results
- **WHEN** user taps a search result row (or its status button) for a movie or series that is already in the library
- **THEN** the client opens the preferences modal populated with the item's current quality profile, monitoring status, and season selections (for series), and upon saving or removing, refreshes the search results to reflect the change
