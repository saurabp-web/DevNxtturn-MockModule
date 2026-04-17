// C:\nxtturn\frontend\cypress.config.cjs

const { defineConfig } = require('cypress')
const fs = require('fs')
const path = require('path')

// Manually parse the .env file for Windows execution,
// but rely on Docker env vars when running in the container.
function getFrontendUrl() {
  // Priority 1: Use CYPRESS_BASE_URL if set by Docker Compose (e.g., https://frontend:5173)
  if (process.env.CYPRESS_BASE_URL) {
    return process.env.CYPRESS_BASE_URL
  }
  // Priority 2: Try to read FRONTEND_URL from the root .env file (for Windows)
  try {
    const envPath = path.resolve(__dirname, '..', '.env')
    const envFile = fs.readFileSync(envPath, 'utf8')
    const match = envFile.match(/FRONTEND_URL=(.*)/)
    if (match && match[1]) {
      return match[1].trim()
    }
  } catch (err) {
    // If .env file is missing or unreadable, fail gracefully later.
  }
  // Priority 3: Hardcoded fallback (should ideally not be reached if env vars are set)
  return 'https://192.168.10.33.nip.io:5173'
}

module.exports = defineConfig({
  e2e: {
    chromeWebSecurity: false,
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    requestTimeout: 15000,

    // --- DYNAMIC BASE URL RESOLUTION ---
    // This correctly prioritizes Docker env vars, then the .env file, then a fallback.
    baseUrl: getFrontendUrl(),

    env: {
      // Use the relative path for API calls, as Vite Proxy handles the base URL.
      VITE_API_BASE_URL: '/api/',
    },

    // --- SECRET HANDSHAKE FOR TESTING EMAIL BACKEND ---
    headers: {
      'X-Cypress-Test': 'true',
    },

    setupNodeEvents(on, config) {
      // Log information for debugging
      console.log(`\n--- Cypress Setup Node Events ---`)
      console.log(`Base URL determined: ${config.baseUrl}`)

      // Environment variable for email backend (if needed by other tests)
      // This variable is read by Django's settings.py and middleware
      config.env.EMAIL_BACKEND =
        process.env.EMAIL_BACKEND || 'django.core.mail.backends.locmem.EmailBackend'

      if (!config.baseUrl) {
        console.error('\n[!] CYPRESS CONFIG ERROR: No valid URL found for baseUrl.')
        console.error('    Please ensure FRONTEND_URL is set in your C:\\nxtturn\\.env file')
        console.error('    or CYPRESS_BASE_URL is set in your docker-compose.yml.')
        throw new Error('Base URL for Cypress is undefined. Cannot proceed.')
      }

      return config
    },
  },
})
