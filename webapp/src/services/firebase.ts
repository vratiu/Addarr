import { initializeApp, getApps } from 'firebase/app';
import { getDatabase } from 'firebase/database';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'demo-api-key',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'addarr-demo',
  databaseURL: import.meta.env.VITE_FIREBASE_DATABASE_URL || 'https://addarr-demo.firebaseio.com',
};

const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
export const database = getDatabase(app);
export const auth = getAuth(app);
