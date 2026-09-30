export const statsData = [
  { label: 'Total Exams', value: 516, trend: '+12 this week', icon: 'graduation', color: '#7C3AED' },
  { label: 'Published Exams', value: 428, trend: '+18 this week', icon: 'file-check', color: '#2563EB' },
  { label: 'Draft Exams', value: 62, trend: '+6 this week', icon: 'pencil', color: '#D97706' },
  { label: 'Under Review', value: 26, trend: '+4 this week', icon: 'clock', color: '#7C3AED' },
  { label: 'Total Tests', value: 1248, trend: '+32 this week', icon: 'book', color: '#059669' },
  { label: 'Total Questions', value: 85430, trend: '+1,245 this week', icon: 'question', color: '#DC2626' },
]

export const recentExams = [
  { name: 'JEE Main 2026', type: 'Entrance Exam', category: 'Engineering', status: 'Published', updatedOn: '18 May 2025' },
  { name: 'NEET UG 2026', type: 'Entrance Exam', category: 'Medical', status: 'Published', updatedOn: '17 May 2025' },
  { name: 'GATE 2026', type: 'Entrance Exam', category: 'Engineering', status: 'Review', updatedOn: '16 May 2025' },
  { name: 'UPSC CSE 2026', type: 'Job Exam', category: 'Civil Services', status: 'Draft', updatedOn: '15 May 2025' },
  { name: 'SSC CGL 2026', type: 'Job Exam', category: 'SSC', status: 'Published', updatedOn: '14 May 2025' },
]

export const examDistribution = [
  { label: 'Entrance Exams', count: 243, percent: 47.1, color: '#7C3AED' },
  { label: 'Job Exams', count: 189, percent: 36.6, color: '#3B82F6' },
  { label: 'School Exams', count: 84, percent: 16.3, color: '#10B981' },
]

export const examTrend = [
  { date: 'May 12', count: 18 },
  { date: 'May 13', count: 25 },
  { date: 'May 14', count: 30 },
  { date: 'May 15', count: 22 },
  { date: 'May 16', count: 20 },
  { date: 'May 17', count: 15 },
  { date: 'May 18', count: 19 },
]

export const recentTestActivity = [
  { name: 'JEE Main Mock Test 01', exam: 'JEE Main 2026', type: 'Mock Test', questions: 90, duration: '180 Min', status: 'Published', updatedOn: '18 May 2025' },
  { name: 'NEET UG Full Test 01', exam: 'NEET UG 2026', type: 'Mock Test', questions: 180, duration: '200 Min', status: 'Published', updatedOn: '17 May 2025' },
  { name: 'GATE CS Practice Test', exam: 'GATE 2026', type: 'Practice Test', questions: 65, duration: '120 Min', status: 'Draft', updatedOn: '16 May 2025' },
  { name: 'SSC CGL PYQ 2025', exam: 'SSC CGL 2026', type: 'Previous Year', questions: 100, duration: '120 Min', status: 'Review', updatedOn: '15 May 2025' },
]

export const navSections = [
  {
    title: 'EXAM ADMIN',
    items: [{ label: 'Dashboard', icon: 'grid', route: '/exam-admin' }],
  },
  {
    title: 'EXAMS',
    items: [
      { label: 'All Exams', icon: 'list', route: '/exam-admin/exams' },
      { label: 'Create Exam', icon: 'plus-circle', route: '/exam-admin/exams/create' },
      { label: 'Draft Exams', icon: 'file', route: '/exam-admin/exams/draft' },
      { label: 'Published Exams', icon: 'check-circle', route: '/exam-admin/exams/published' },
      { label: 'Archived Exams', icon: 'archive', route: '/exam-admin/exams/archived' },
    ],
  },
  {
    title: 'EXAM CLASSIFICATION',
    items: [
      { label: 'Exam Type', icon: 'tag', route: '/exam-admin/classification/type' },
      { label: 'Exam Category', icon: 'folder', route: '/exam-admin/classification/category' },
      { label: 'Exam Level', icon: 'bar-chart', route: '/exam-admin/classification/level' },
      { label: 'Conducting Body', icon: 'building', route: '/exam-admin/classification/body' },
    ],
  },
  {
    title: 'ACADEMIC MAPPING',
    items: [
      { label: 'Education Level', icon: 'graduation', route: '/exam-admin/academic/level' },
      { label: 'Stream', icon: 'git-branch', route: '/exam-admin/academic/stream' },
      { label: 'Field', icon: 'layers', route: '/exam-admin/academic/field' },
      { label: 'Sub Field', icon: 'git-merge', route: '/exam-admin/academic/subfield' },
    ],
  },
  {
    title: 'SYLLABUS',
    items: [
      { label: 'Subjects', icon: 'book-open', route: '/exam-admin/syllabus/subjects' },
      { label: 'Chapters', icon: 'bookmark', route: '/exam-admin/syllabus/chapters' },
      { label: 'Topics', icon: 'map-pin', route: '/exam-admin/syllabus/topics' },
    ],
  },
  {
    title: 'TESTS',
    items: [
      { label: 'Question Bank', icon: 'clipboard', route: '/exam-admin/questions' },
      { label: 'Test Patterns', icon: 'layout', route: '/exam-admin/tests/patterns' },
      { label: 'Test Definitions', icon: 'file-text', route: '/exam-admin/tests/definitions' },
      { label: 'Mock Tests', icon: 'file-text', route: '/exam-admin/tests/mock' },
      { label: 'Practice Tests', icon: 'edit', route: '/exam-admin/tests/practice' },
      { label: 'Previous Year Tests', icon: 'calendar', route: '/exam-admin/tests/previous' },
    ],
  },
  {
    title: 'EXAM SETTINGS',
    items: [
      { label: 'Visibility', icon: 'eye', route: '/exam-admin/settings/visibility' },
      { label: 'Status', icon: 'toggle-right', route: '/exam-admin/settings/status' },
      { label: 'Exam Logo', icon: 'image', route: '/exam-admin/settings/logo' },
      { label: 'Instructions', icon: 'info', route: '/exam-admin/settings/instructions' },
      { label: 'SEO / Display Settings', icon: 'settings', route: '/exam-admin/settings/seo' },
    ],
  },
]