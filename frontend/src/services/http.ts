// src/services/http.ts
//
// CHANGED: this used to be its own axios.create() instance with the
// auth interceptor left commented out as a TODO — every request made
// through it (including examWizardApi.ts's POST /exams/) went out
// with NO Authorization header at all, which is exactly why the
// wizard's publish/save-draft calls got 401 "Authentication
// credentials were not provided" while every other admin API call
// (education-levels, streams, fields, etc. — all made via adminApi.ts
// -> axiosInstance.ts) worked fine.
//
// Fix: re-export the app's real axiosInstance (Knox token auth,
// offline-toast handling, 401 auto-logout — see axiosInstance.ts) so
// examWizardApi.ts automatically gets the same authenticated behavior
// as the rest of the app, instead of maintaining a second, divergent
// axios setup.
import axiosInstance from '@/services/axiosInstance'

export const http = axiosInstance