# telegram-mini-app/bridge Specification Delta

## MODIFIED Requirements

### Requirement: Command Dispatch and Response Handling
The bridge SHALL execute dispatched actions locally against media services and return responses to the cloud broker.

#### Scenario: Command execution round-trip
- **WHEN** a valid `search_movie` command is received by the bridge
- **THEN** the bridge executes the query against local Radarr and writes the formatted result payload back to the response queue

#### Scenario: Calendar movies command execution
- **WHEN** a valid `get_calendar_movies` command is received from an authorized user
- **THEN** the bridge queries local Radarr for upcoming digital releases within the next 60 days (up to 20 items) and writes the result list back to the response queue

#### Scenario: Calendar series command execution
- **WHEN** a valid `get_calendar_series` command is received from an authorized user
- **THEN** the bridge queries local Sonarr for upcoming episode releases within the next 60 days (grouped by same-day series drops and capped at 20 items) and writes the result list back to the response queue
