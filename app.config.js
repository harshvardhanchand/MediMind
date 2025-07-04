import 'dotenv/config';

export default {
  "expo": {
    "name": "MediMind",
    "slug": "medical-data-hub",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./frontend/assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./frontend/assets/splash-icon.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "assetBundlePatterns": [
      "frontend/**/*"
    ],
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.harshchand.medimind",
      "infoPlist": {
        "ITSAppUsesNonExemptEncryption": false
      },
      "associatedDomains": [
        "applinks:medimind.co.in",
        "applinks:www.medimind.co.in"
      ]
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./frontend/assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.harshchand.medimind"
    },
    "web": {
      "favicon": "./frontend/assets/favicon.png"
    },
    "scheme": "medimind",
    "plugins": [
      "expo-secure-store",
      "expo-document-picker",
      "expo-file-system",
      [
        "expo-notifications",
        {
          "icon": "./frontend/assets/notification-icon.png",
          "color": "#ffffff",
          "defaultChannel": "default"
        }
      ]
    ],
    "notification": {
      "icon": "./frontend/assets/notification-icon.png",
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