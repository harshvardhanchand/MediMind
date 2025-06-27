import 'dotenv/config';

export default {
  "expo": {
    "name": "MediMind",
    "slug": "medical-data-hub",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./assets/splash-icon.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "assetBundlePatterns": [
      "**/*"
    ],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.harshchand.medimind",
      "infoPlist": {
        "ITSAppUsesNonExemptEncryption": false
      }
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.harshchand.medimind"
    },
    "web": {
      "favicon": "./assets/favicon.png"
    },
    "scheme": "medimind",
    "plugins": [
      "expo-secure-store",
      "expo-document-picker",
      "expo-file-system",
      "expo-build-properties",
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#ffffff",
          "defaultChannel": "default"
        }
      ]
    ],
    "notification": {
      "icon": "./assets/notification-icon.png",
      "color": "#ffffff",
      "iosDisplayInForeground": true,
      "androidMode": "default",
      "androidCollapsedTitle": "MediMind Alert"
    },
    "extra": {
      "supabaseUrl": process.env.SUPABASE_URL,
      "supabaseAnonKey": process.env.SUPABASE_ANON_KEY,
      "apiUrl": process.env.API_URL,
      "sentryDsn": process.env.SENTRY_DSN,
      "eas": {
        "projectId": "1d4df6d4-eb0c-41b2-b0df-5d68fbda7ba6"
      }
    }
  }
}
