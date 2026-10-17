# telegram-mini-app/client Specification Delta

## ADDED Requirements

### Requirement: Calendar Tab Navigation and Media Type Persistence
The client SHALL provide a "Calendar" tab alongside "Search & Add" and "My Library" that displays upcoming releases for the selected media type and retains the active tab when switching between Movies and Series.

#### Scenario: Switch from Movies to Series while on Calendar tab
- **WHEN** user is viewing the "Calendar" tab with "Movies" selected and clicks the "Series" media type toggle
- **THEN** the client remains on the "Calendar" tab and loads upcoming series episode releases without resetting to "Search & Add"

#### Scenario: Switch from Series to Movies while on Calendar tab
- **WHEN** user is viewing the "Calendar" tab with "Series" selected and clicks the "Movies" media type toggle
- **THEN** the client remains on the "Calendar" tab and loads upcoming digital movie releases

### Requirement: Upcoming Release List and Relative Date Formatting
The client SHALL render upcoming calendar entries in a chronological list (up to 60 days and at most 20 entries) showing the formatted release date and a relative day indicator for releases occurring in fewer than 14 days.

#### Scenario: Display release date less than 14 days away
- **WHEN** a calendar entry has a release date fewer than 14 days from the current date (e.g., 3 days from today)
- **THEN** the client displays both the formatted calendar date and the relative day offset (e.g., `(in 3 days)`, `(tomorrow)`, or `(today)`)

#### Scenario: Display release date 14 or more days away
- **WHEN** a calendar entry has a release date between 14 and 60 days from the current date
- **THEN** the client displays the formatted calendar date without a relative day suffix
