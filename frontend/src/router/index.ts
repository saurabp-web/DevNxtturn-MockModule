import { createRouter, createWebHistory } from 'vue-router'
import 'vue-router'
import { useAuthStore } from '@/stores/auth'
import CommunityLayout from '@/layouts/CommunityLayout.vue'
import MessagingLayout from '@/layouts/MessagingLayout.vue'
import ProfileLayout from '@/layouts/ProfileLayout.vue'
import ExploreLayout from '@/layouts/ExploreLayout.vue'
import ExamLayout from '@/layouts/ExamLayout.vue'

import CheckEmailView from '../views/auth/CheckEmailView.vue'
import ForgotPasswordView from '../views/auth/ForgotPasswordView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
  }
}

// In your router/index.ts or router.js

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // --- ROUTE GROUP 1: Uses the 3-Column Community Layout ---
    {
      path: '/',
      component: CommunityLayout,
      children: [
        {
          path: '',
          name: 'feed',
          component: () => import('@/views/FeedView.vue'),
          meta: { requiresAuth: false }, // Guests can now load the homepage feed! [3]
        },
        {
          path: 'groups',
          name: 'group-list',
          component: () => import('@/views/GroupListAllView.vue'),
        },
        {
          path: 'groups/:slug',
          name: 'group-detail',
          component: () => import('@/views/GroupDetailView.vue'),
        },
        {
          path: 'groups/:slug/requests',
          name: 'group-requests',
          component: () => import('@/views/GroupRequestsView.vue'),
          meta: { requiresAuth: true }, // PRIVATE: requires login [1.1.2]
        },
        {
          path: 'saved-posts',
          name: 'saved-posts',
          component: () => import('@/views/SavedPostsView.vue'),
          meta: { requiresAuth: true }, // PRIVATE: requires login [1.1.2]
        },
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/views/NotificationsPage.vue'),
          meta: { requiresAuth: true }, // PRIVATE: requires login [1.1.2]
        },
        {
          path: 'network',
          name: 'network',
          component: () => import('@/views/NetworkView.vue'),
          meta: { requiresAuth: true }, // PRIVATE: requires login [1.1.2]
        },
        { path: 'search', name: 'search', component: () => import('@/views/SearchPage.vue') },
        {
          path: 'posts/:postId',
          name: 'single-post',
          component: () => import('@/views/SinglePostView.vue'),
        },
      ],
    },
    // --- ROUTE GROUP 2: Uses the Profile Layout ---
    {
      path: '/profile',
      component: ProfileLayout,
      children: [
        {
          path: ':username',
          name: 'profile',
          component: () => import('@/views/ProfileView.vue'),
          meta: { requiresAuth: false }, // PUBLIC [4]
        },
      ],
    },
    {
      path: '/messages',
      component: MessagingLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'messages',
          component: () => import('@/views/MessagingViews.vue'),
        },
      ],
    },
    {
      path: '/chat',
      redirect: { name: 'messages' },
    },
    // --- ROUTE GROUP 3: Uses the Explore Layout ---
    {
      path: '/explore',
      component: ExploreLayout,
      children: [
        {
          path: '',
          name: 'explore',
          component: () => import('@/views/ExploreView.vue'),
          meta: { requiresAuth: false }, // PUBLIC [3]
        },
      ],
    },
    // --- ROUTE GROUP: Uses the dedicated Exam Layout (no community sidebars) ---
        {
      path: '/exams',
      component: ExamLayout,
      children: [
        { path: '', name: 'exams', component: () => import('@/views/ExamView.vue'), meta: { requiresAuth: false } },

        // Practice flow landing page (Quick Actions: Practice / Custom / Mock)
        {
          path: 'practice',
          name: 'practice-start',
          component: () => import('@/views/practice/PracticeStartView.vue'),
        },

        // After the existing 'exams' route entry, add these:
        {
          path: 'practice/exam-type',
          name: 'practice-exam-type',
          component: () => import('@/views/practice/SelectExamTypeView.vue'),
        },
        {
          path: 'practice/test-type',
          name: 'practice-test-type',
          component: () => import('@/views/practice/SelectTestTypeView.vue'),
        },
        {
          path: 'practice/subject',
          name: 'practice-subject',
          component: () => import('@/views/practice/SelectSubjectView.vue'),
        },
        {
          path: 'practice/scope',
          name: 'practice-scope',
          component: () => import('@/views/practice/SelectScopeView.vue'),
        },
        {
          path: 'practice/chapter',
          name: 'practice-chapter',
          component: () => import('@/views/practice/SelectChapterView.vue'),
        },
        {
          path: 'practice/mode',
          name: 'practice-mode',
          component: () => import('@/views/practice/SelectModeView.vue'),
        },
        {
          path: 'practice/review',
          name: 'practice-review',
          component: () => import('@/views/practice/ReadyToStartView.vue'),
        },
        {
          path: 'practice/full-syllabus',
          name: 'practice-full-syllabus',
          component: () => import('@/views/practice/Completesyllabusview.vue'),
        },
        {
          path: 'practice/custom-result',
          name: 'practice-custom-result',
          component: () => import('@/views/practice/Customtestresultview.vue'),
        },
        {
          path: 'practice/test',
          name: 'practice-test',
          component: () => import('@/views/practice/TestAttemptView.vue'),
        },
        {
          path: 'practice/custom',
          name: 'practice-custom',
          component: () => import('@/views/practice/Createcustomtestview.vue'),
        },
        { path: 'practice/mock/select',
          name: 'mock-select',       
          component: () => import('@/views/practice/Selectmocktestview.vue'),
        },
        { path: 'practice/mock/instructions',
          name: 'mock-instructions', 
          component: () => import('@/views/practice/MockInstructionsView.vue'),
        },
        { path: 'practice/mock/attempt',
          name: 'mock-attempt',      
          component: () => import('@/views/practice/Mocktestattemptview.vue'),
        },
      ],
    },
        // --- ROUTE GROUP: Exam attempt (standalone, no shared layout) ---
    // {
    //   path: '/exams/:id',
    //   name: 'exam-attempt',
    //   component: () => import('@/views/TestAttemptView.vue'),
    //   props: true,
    //   meta: { requiresAuth: false }, // adjust to true if attempts require login
    // },
    // --- ROUTE GROUP 4: Non-Layout Routes (Login/Register) ---
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/auth/check-email',
      name: 'CheckEmail',
      component: CheckEmailView,
      meta: { requiresGuest: true },
    },

    {
      path: '/verify-email/:key',
      name: 'VerifyEmail',
      // Since you created the file in views/VerifyEmailView.vue:
      component: () => import('@/views/VerifyEmailView.vue'),
      meta: { requiresGuest: true },
    },

    {
      path: '/auth/forgot-password',
      name: 'ForgotPassword',
      component: ForgotPasswordView,
      meta: { requiresGuest: true },
    },
    // --- THIS IS THE NEW ROUTE WE ARE ADDING ---
    {
      path: '/auth/reset-password/:uid/:token',
      name: 'ResetPasswordConfirm',
      component: () => import('@/views/auth/ResetPasswordConfirmView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/profile/:username/posts',
      name: 'UserPosts',
      component: () => import('@/views/UserPostsPage.vue'),
      props: true,
      meta: {
        title: 'User Posts',
        requiresAuth: false,
      },
    },
    {
      path: '/privacy',
      name: 'privacy-policy',
      component: () => import('@/views/PrivacyPolicyView.vue'),
      meta: {
        title: 'Privacy Policy',
        requiresAuth: false, // PUBLIC: indexable on Google! [3]
      },
    },
    // --- ROUTE GROUP 5: Uses the clean full-width Profile Layout (No Sidebars) --- [1]
    {
      path: '/settings',
      component: ProfileLayout,
      children: [
        {
          path: '',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
          meta: { requiresAuth: true }, // PRIVATE [4]
        },
      ],
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  await authStore.initializeAuth()
  const isAuthenticated = authStore.isAuthenticated

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' })
  } else if (to.meta.requiresGuest && isAuthenticated) {
    next({ name: 'feed' })
  } else {
    next()
  }
})

export default router