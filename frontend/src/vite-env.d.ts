/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_WEATHER_API_KEY?: string;
  readonly VITE_TWITTER_TRENDS_API_KEY?: string;
  readonly WEATHER_API_KEY?: string;
  readonly Twitter_Trends_API_KEY?: string;
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
