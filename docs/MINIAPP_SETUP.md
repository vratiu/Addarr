# Addarr Telegram Mini App Setup Guide (Dev & Prod)

This guide walks you step-by-step through setting up, developing, and deploying the **Addarr Telegram Mini App (TMA)** on top of your existing Addarr homelab installation.

---

## Architecture Overview

```
+-------------------------------------------------------------+
| Telegram (Client / Phone)                                   |
|   Mini App Webview (Hosted on Firebase Hosting CDN)          |
+-------------------------------------------------------------+
                              |
                              | HTTPS / Realtime Events
                              v
+-------------------------------------------------------------+
| Google Cloud / Firebase Realtime Database (Free Tier)       |
|   /requests/{userId}/{reqId}   <-- Mini App writes          |
|   /responses/{userId}/{reqId}  --> Mini App reads           |
+-------------------------------------------------------------+
                              ^
                              | Outbound Event Listener
                              | (Zero tunnels, zero open ports)
+-------------------------------------------------------------+
| Homelab Host (Behind NAT / Router)                          |
|   Addarr Python Daemon                                      |
|     - Local requests to Radarr (:7878) and Sonarr (:8989)   |
|     - Executes Search, Add, Update Preferences, Browse      |
+-------------------------------------------------------------+
```

---

## 1. Firebase Cloud Setup (100% Free Tier)

Both Development and Production use Firebase Realtime Database as a serverless, zero-maintenance message bridge.

### Step 1.1: Create a Firebase Project
1. Log in to the [Firebase Console](https://console.firebase.google.com/) with your Google account.
2. Click **Create a project** (or **Add project**).
3. Name your project (e.g., `addarr-miniapp-prod`).
4. You can disable Google Analytics (not required) and click **Create Project**.
5. Ensure your project is on the **Spark Plan (Free)**.

### Step 1.2: Set Up Realtime Database
1. In the Firebase console left menu, go to **Build** $\rightarrow$ **Realtime Database**.
2. Click **Create Database**.
3. Select your preferred database region (e.g., `United States` or `Belgium (europe-west1)`).
4. Select **Start in locked mode** and click **Enable**.
5. Note your database URL. It looks like:
   `https://<your-project-id>-default-rtdb.firebaseio.com`

### Step 1.3: Apply Security Rules
1. In Realtime Database, click the **Rules** tab.
2. Replace the default rules with the contents of [`firebase/database.rules.json`](../firebase/database.rules.json):
   ```json
   {
     "rules": {
       "requests": {
         "$uid": {
           ".read": "auth != null && auth.uid == $uid",
           ".write": "auth != null && auth.uid == $uid",
           "$reqId": {
             ".validate": "newData.hasChildren(['action', 'payload'])"
           }
         }
       },
       "responses": {
         "$uid": {
           ".read": "auth != null && auth.uid == $uid",
           ".write": false
         }
       },
       "users": {
         "$uid": {
           ".read": "auth != null && auth.uid == $uid",
           ".write": "auth != null && auth.uid == $uid"
         }
       }
     }
   }
   ```
3. Click **Publish**.

### Step 1.4: Generate Service Account Key for Addarr
1. Click the **Gear icon (Project Settings)** in the top left.
2. Go to the **Service accounts** tab.
3. Select **Firebase Admin SDK** (Python is selected by default).
4. Click **Generate new private key** $\rightarrow$ **Generate key**.
5. A JSON file will download. Rename this file to:
   `serviceAccountKey.json`
6. Place this file inside your Addarr root folder (`/Users/virgil/work/Addarr/serviceAccountKey.json`).
   *(Note: This file is already excluded in `.gitignore` and must never be committed to git).*

### Step 1.5: Copy Web App Configuration
1. In **Project Settings** $\rightarrow$ **General** tab, scroll to **Your apps**.
2. Click the **Web (`</>`)** icon to register a web app.
3. Enter an app nickname (e.g., `Addarr Mini App`) and click **Register app**.
4. You will see your Firebase SDK snippet. Copy the values:
   - `apiKey`
   - `projectId`
   - `databaseURL`

---

## 2. Local Development Setup (Dev Mode)

### Step 2.1: Addarr Backend (Homelab)
1. Ensure your Python virtual environment is active:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. In your `config.yaml`, enable the `miniapp` block:
   ```yaml
   miniapp:
     enable: true
     url: "http://localhost:3000" # Local dev frontend
     databaseURL: "https://<your-project-id>-default-rtdb.firebaseio.com"
     serviceAccountPath: "serviceAccountKey.json"
   ```
3. Run Addarr:
   ```bash
   python src/addarr.py
   ```
   Verify console log shows:
   ```text
   INFO - Firebase Admin initialized successfully for Mini App bridge.
   INFO - Mini App bridge is actively listening for incoming requests.
   ```

### Step 2.2: Mini App Frontend (Vite Dev Server)
1. Open a new terminal in the `webapp/` folder:
   ```bash
   cd webapp
   ```
2. Create your local environment file `webapp/.env.local`:
   ```bash
   VITE_FIREBASE_API_KEY="AIzaSy..."
   VITE_FIREBASE_PROJECT_ID="<your-project-id>"
   VITE_FIREBASE_DATABASE_URL="https://<your-project-id>-default-rtdb.firebaseio.com"
   ```
3. Install frontend dependencies:
   ```bash
   npm install
   ```
4. Start the local development server:
   ```bash
   npm run dev
   ```
5. Open `http://localhost:3000` in your browser.
   * You can test searching, adding, browsing, and changing preferences directly from your local browser!

---

## 3. Production Deployment (Prod Mode)

In production, the Mini App is served from Google's global CDN via **Firebase Hosting** (free, includes auto-renewing SSL), and Addarr runs as a Docker container or systemd service on your homelab server.

### Step 3.1: Deploy Mini App to Firebase Hosting
1. Install the Firebase CLI globally (if not installed):
   ```bash
   npm install -g firebase-tools
   ```
2. Log in to Firebase:
   ```bash
   firebase login
   ```
3. From the `webapp/` directory, initialize hosting:
   ```bash
   cd webapp
   firebase init hosting
   ```
   * Choose: **Use an existing project** $\rightarrow$ Select your Firebase project.
   * Public directory: `dist`
   * Configure as a single-page app: `Yes`
   * Set up automatic builds with GitHub: `No` (optional)
   * Overwrite `dist/index.html`: `No`
4. Build the production bundle:
   ```bash
   npm run build
   ```
5. Deploy to Firebase Hosting:
   ```bash
   firebase deploy --only hosting
   ```
6. Firebase will output your live URL:
   `Hosting URL: https://<your-project-id>.web.app`

### Step 3.2: Configure Addarr with Production URL
Update your homelab `config.yaml`:
```yaml
miniapp:
  enable: true
  url: "https://<your-project-id>.web.app" # Production Firebase Hosting URL
  databaseURL: "https://<your-project-id>-default-rtdb.firebaseio.com"
  serviceAccountPath: "serviceAccountKey.json"
```

### Step 3.3: Production Docker Deployment for Addarr
When running Addarr in Docker, mount `serviceAccountKey.json` into the container alongside `config.yaml`:

```yaml
# docker-compose.yml example:
version: "3.7"
services:
  addarr:
    build: .
    container_name: addarr
    restart: unless-stopped
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./serviceAccountKey.json:/app/serviceAccountKey.json:ro
      - ./admin.txt:/app/admin.txt:ro
      - ./allowlist.txt:/app/allowlist.txt:ro
      - ./chatid.txt:/app/chatid.txt:rw
      - ./logs:/app/logs:rw
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/serviceAccountKey.json
```
Deploy the container:
```bash
docker compose up -d --build
```

---

## 4. Connecting the Mini App in Telegram

You have two convenient ways to access your Mini App in Telegram:

### Method A: In-Chat Command (`/app`)
* Send `/app` in chat with your bot.
* The bot sends an inline message with a **🚀 Open Addarr Mini App** button.
* Tapping it launches the web app in the Telegram webview.

### Method B: Persistent Menu Button (Recommended)
You can configure Telegram so a permanent button appears directly next to the message input box in your bot chat:

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/setmenubutton`.
3. Select your Addarr bot.
4. Send the button URL:
   `https://<your-project-id>.web.app`
5. Send the button label:
   `Open Addarr`
6. Now, whenever you open your chat with your bot, a persistent **"Open Addarr"** button is displayed next to the attachment icon!

---

## 5. Troubleshooting & FAQ

* **Q: Mini App says "Connecting to Addarr homelab bridge..."**
  * *Cause:* Addarr is not currently running, or `miniapp.enable` is false in `config.yaml`.
  * *Fix:* Check `python src/addarr.py` logs or `docker logs addarr` to ensure the bridge initialized successfully.

* **Q: "Permission Denied" in browser console when writing requests**
  * *Cause:* Firebase Realtime Database rules reject unauthenticated writes.
  * *Fix:* In development, you can test with custom token auth or ensure `database.rules.json` matches the authorized user rules.

* **Q: Do I need to open ports 7878 (Radarr) or 8989 (Sonarr) on my router?**
  * *No.* Addarr and your *arr apps remain strictly on your local network. Addarr connects outbound to Firebase to receive commands, executes them on your LAN, and pushes responses back out.
