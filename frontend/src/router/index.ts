import { createRouter, createWebHistory } from 'vue-router'
import 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { fetchAdminSessionUser, redirectToDjangoAdminLogin } from '@/services/adminAuth'
import CommunityLayout from '@/layouts/CommunityLayout.vue'
import MessagingLayout from '@/layouts/MessagingLayout.vue'
import ProfileLayout from '@/layouts/ProfileLayout.vue'
import ExploreLayout from '@/layouts/ExploreLayout.vue'
import ExamLayout from '@/layouts/ExamLayout.vue'
import AdminLayout from '@/components/admin/AdminLayout.vue'

import CheckEmailView from '../views/auth/CheckEmailView.vue'
import ForgotPasswordView from '../views/auth/ForgotPasswordView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
    requiresAdmin?: boolean
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
    // --- ROUTE GROUP: Admin Panel ---
    // CHANGED: path moved from '/admin' to '/exam-admin' so it never
    // collides with Django's built-in admin site, which lives at the
    // normal '/admin/' path (see config/urls.py and vite.config.ts).
    // Route names are unchanged, so any router.push({ name: 'admin-dashboard' })
    // calls elsewhere in the app still work without edits.
    {
      path: '/exam-admin',
      component: AdminLayout,
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/DashboardView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'exams',
          name: 'admin-exams',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
        {
          path: 'exams/create',
          name: 'admin-exam-create',
          component: () => import('@/views/admin/exams/CreateExamView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'exams/draft',
          name: 'admin-exams-draft',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
        {
          path: 'exams/published',
          name: 'admin-exams-published',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
        {
          path: 'exams/archived',
          name: 'admin-exams-archived',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
        {
          path: 'tests/mock',
          name: 'admin-tests-mock',
          component: () => import('@/views/admin/tests/Mocktestsview.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'tests/mock/create',
          name: 'admin-mock-test-create',
          component: () => import('@/views/admin/tests/CreateMockTestView.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'tests/practice',
          name: 'admin-tests-practice',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
        // --- Previous Year Tests flow (7-step admin process) ---
        {
          path: 'tests/previous',
          name: 'admin-tests-previous',
          component: () => import('@/views/admin/pyq-test/SelectPYTest.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'tests/previous/upload',
          name: 'admin-tests-previous-upload',
          component: () => import('@/views/admin/pyq-test/UploadExtractPDF.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'tests/previous/map-paper-details',
          name: 'admin-tests-previous-map-paper-details',
          component: () => import('@/views/admin/pyq-test/MapPaperDetails.vue'),
          meta: { requiresAuth: true },
        },
        {
          // Step 3 of the PYQ import wizard. This route was missing —
          // MapPaperDetails.vue's "Next" button and ReviewCreateTest.vue's
          // "Back" button both already push to this name, so they were
          // throwing "No match for {name: ...}" instead of navigating.
          path: 'tests/previous/review-questions',
          name: 'admin-tests-previous-review-questions',
          component: () => import('@/views/admin/pyq-test/ReviewExtractedQuestions.vue'),
          meta: { requiresAuth: true },
        },
        
        {
          path: 'tests/previous/review-create',
          name: 'admin-tests-previous-review-create',
          component: () => import('@/views/admin/pyq-test/ReviewCreateTest.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'tests/previous/extract-questions',
          name: 'admin-tests-previous-extract-questions',
          component: () => import('@/views/admin/pyq-test/ExtractQuestions.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'tests/previous/configure-publish',
          name: 'admin-tests-previous-configure-publish',
          component: () => import('@/views/admin/pyq-test/ConfigureTestPublish.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'tests/previous/published',
          name: 'admin-tests-previous-published',
          component: () => import('@/views/admin/pyq-test/TestPublished.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'settings/visibility',
          name: 'admin-settings-visibility',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
        {
          path: 'settings/seo',
          name: 'admin-settings-seo',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
        // --- Syllabus → Subjects ---
        {
          path: 'syllabus/subjects',
          name: 'admin-subjects',
          component: () => import('@/views/admin/subject/Subjectslistview.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'syllabus/subjects/create',
          name: 'admin-subjects-create',
          component: () => import('@/views/admin/subject/Addsubjectview.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'syllabus/subjects/:id/edit',
          name: 'admin-subjects-edit',
          component: () => import('@/views/admin/subject/Addsubjectview.vue'),
          props: true,
          meta: { requiresAuth: true },
        },
        // --- Syllabus → Chapters / Topics (placeholders until built) ---
        {
          path: 'syllabus/chapters',
          name: 'admin-chapters',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
        {
          path: 'syllabus/topics',
          name: 'admin-topics',
          component: () => import('@/views/admin/DashboardView.vue'), // placeholder
          meta: { requiresAuth: true },
        },
      ],
    },
    // --- ROUTE GROUP: Question Bank (nested under Exam Admin, same sidebar/layout) ---
    {
      path: '/exam-admin/questions',
      component: AdminLayout,
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'question-bank',
          component: () => import('@/views/admin/question/QuestionBank.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'add',
          name: 'question-add',
          component: () => import('@/views/admin/question/AddQuestion.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'review',
          name: 'question-review',
          component: () => import('@/views/admin/question/QuestionReview.vue'),
          meta: { requiresAuth: true },
        },
        // --- Import Questions flow (Question Bank) ---
        // CHANGED: this used to mount ImportQuestionsUpload.vue directly
        // (dead emit, no listener), then later called the mock-exam
        // bulk-upload endpoints via ImportQuestionsWizard.vue with an
        // examId pulled from ?examId= in the query string — but nothing
        // ever set that query param when linking here, so it was always
        // undefined. QuestionBankImportWizard.vue now has its own Step 0
        // ("Select Exam") that asks for the exam directly, so this route
        // no longer needs to receive examId at all.
       {
          path: 'questions/import',
          name: 'question-import',
          // All wizard files must be in this exact folder:
          // src/views/admin/import-questions/
          component: () => import('@/views/admin/import-questions/QuestionBankImportWizard.vue'),
          meta: { requiresAuth: true },
        },
      ],
    },
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
  // Admin routes are gatekept by Django's own session (via /admin/login/),
  // not the app-wide token auth used everywhere else — checked separately.
  if (to.meta.requiresAdmin) {
    const adminUser = await fetchAdminSessionUser()
    if (!adminUser || !adminUser.is_staff) {
      redirectToDjangoAdminLogin(to.fullPath)
      return // full page redirect, no need to call next()
    }
    next()
    return
  }

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