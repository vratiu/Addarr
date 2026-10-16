# Tasks

## 1. Backend: Sonarr & Radarr Library Mutations & Queries

- [x] 1.1 Implement `get_library_summary` in `src/radarr.py` and `src/sonarr.py` to fetch streamlined media records (id, title, year, poster URL, profileId, monitored, status) and verify with mock unit tests.
- [x] 1.2 Implement `update_movie` in `src/radarr.py` using `PUT /api/v3/movie/{id}` to update quality profiles and monitored status, and verify using mock API tests.
- [x] 1.3 Implement `update_series` in `src/sonarr.py` using `PUT /api/v3/series/{id}` to update quality profiles, monitored status, and season monitoring selections, and verify using mock API tests.

## 2. Backend: Outbound Bridge Module

- [x] 2.1 Add `miniapp` configuration block to `config_example.yaml` and validation in `src/config.py`, verifying config checks handle enabled/disabled states cleanly.
- [x] 2.2 Add Firebase Admin SDK dependency to `requirements.txt` and update `Dockerfile` to include necessary credentials path.
- [x] 2.3 Implement `src/bridge.py` to establish the outbound event listener to Firebase RTDB, validate user authorization against `allowlist.txt`/`admin.txt`, dispatch commands to Sonarr/Radarr, and post responses. Verify with unit tests using mocked Firebase events.
- [x] 2.4 Integrate the bridge runner into `src/addarr.py` startup so it runs concurrently with `Application.run_polling()`.

## 3. Cloud: Firebase Security Rules & Auth Function

- [x] 3.1 Create `firebase/database.rules.json` locking down `/users/$uid` strictly to authenticated users with `auth.uid == $uid`, and verify rules syntax.
- [x] 3.2 Implement the Telegram `initData` HMAC-SHA256 signature verification and Firebase custom token issuance handler in `cloud/auth/`.

## 4. Frontend: Telegram Mini App Client

- [x] 4.1 Scaffold the Mini App project (`webapp/`) with Vite, React, Tailwind CSS, and `@telegram-apps/sdk`, and verify static production build output (`npm run build`).
- [x] 4.2 Implement Firebase RTDB bridge client service in `webapp/src/services/bridge.ts` to dispatch requests and listen for responses on the user's private node.
- [x] 4.3 Implement Search & Quick-Add screen: live search input, poster cards, and single-screen modal to pick quality profile and folder in 1 tap.
- [x] 4.4 Implement Library Browser screen: filterable poster grid (All, Downloaded, Missing, Unmonitored) with instant search and sorting.
- [x] 4.5 Implement Media Preference Editor modal: quality profile switcher, monitored toggle, and granular season checkboxes for series.

## 5. Integration & Verification

- [x] 5.1 Add `/app` command and inline keyboard button in `src/addarr.py` sending a `WebAppInfo` button to launch the Mini App inside Telegram.
- [x] 5.2 Perform end-to-end verification: launch Mini App, search for a title, execute 1-tap add, view in library, and update season preferences.
