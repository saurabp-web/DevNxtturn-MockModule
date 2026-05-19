import axiosInstance from '@/services/axiosInstance'

// Chat uses the shared authenticated axios client so it inherits the same
// base URL, token handling, and backend-host URL sanitization.
const chatApi = axiosInstance

export default chatApi
