import axios, { type AxiosInstance } from 'axios'

// NOTE: matches your StudentExamViewSet. Adjust baseURL/path if your
// router registers it under a different prefix (e.g. router.register('exams', ...)).
const api: AxiosInstance = axios.create({
  baseURL: '/api',
})

export default api
