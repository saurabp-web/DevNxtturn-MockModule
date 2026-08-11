import { defineStore } from 'pinia'

export interface CustomConfig {
  subjectIds:       string[] | 'all'
  subjectLabel:     string
  durationMinutes:  number
  difficulty:       string
  totalMarks:       number
  numQuestions:     number
  marksPerQuestion: number
}

export interface CustomTestResult {
  testName:         string
  subjectName:      string
  score:            number
  total:            number
  percentage:       number
  correct:          number
  wrong:            number
  skipped:          number
  attempted:        number
  timeTakenSeconds: number
  totalTimeSeconds: number
  submittedAt:      string   // ISO date string
}


export interface MockTest {
  id: number
  name: string
  questions: number
  duration: string
  marks: number
  difficulty: 'Easy' | 'Medium' | 'Hard'
  language: string
  attempted: boolean
  isLatest?: boolean
}
export interface PracticeExam {
  id: string
  label: string
  category: string   // e.g. 'JEE', 'NEET' — used for API calls
}

export interface PracticeExamType {
  id: string
  label: string
  dbId?: number | null   // real numeric Exam PK, resolved from the backend
                          // once the user confirms this exam type. Required
                          // by SelectSubjectView's /subjects/ API call.
}

export interface PracticeSubject {
  id: string
  label: string
  testCount: number
  icon: string
}

export interface PracticeChapter {
  id: string
  label: string
  questionCount: number
}

export type PracticeScope = 'chapter' | 'full' | null
export type PracticeMode = 'test' | 'practice' | null

interface PracticeTestState {
  exam: PracticeExam | null
  examType: PracticeExamType | null
  testType: 'practice' | 'custom' | 'mock' | null
  subject: PracticeSubject | null
  scope: PracticeScope
  chapter: PracticeChapter | null
  mode: PracticeMode
  customConfig: CustomConfig | null
  customTestResult: CustomTestResult | null
  mockTest: MockTest | null
}

export const usePracticeTestStore = defineStore('practiceTest', {
  state: (): PracticeTestState => ({
    exam: null,
    examType: null,
    testType: null,
    subject: null,
    scope: null,
    chapter: null,
    mode: null,
    customConfig: null,
    customTestResult: null,
    mockTest: null,
  }),
  getters: {
    questionCount: (state) => state.chapter?.questionCount ?? 18,
    durationMinutes: () => 45,
    difficulty: () => 'Medium',
  },
  actions: {
    setExam(exam: PracticeExam) {
      this.exam = exam
      // reset everything downstream when exam changes
      this.examType = null
      this.testType = null
      this.subject = null
      this.scope = null
      this.chapter = null
      this.mode = null
      this.customConfig = null
      this.customTestResult = null
    },
    setExamType(examType: PracticeExamType) {
      this.examType = examType
      this.testType = null
      this.subject = null
      this.scope = null
      this.chapter = null
      this.mode = null
      this.customConfig = null
      this.customTestResult = null
    },
    setSubject(subject: PracticeSubject) {
      this.subject = subject
      this.scope = null
      this.chapter = null
      this.mode = null
    },
    setScope(scope: PracticeScope) {
      this.scope = scope
      this.chapter = null
      this.mode = null
    },
    setChapter(chapter: PracticeChapter) {
      this.chapter = chapter
      this.mode = null
    },
    setMode(mode: PracticeMode) {
      this.mode = mode
    },
    setTestType(type: 'practice' | 'custom' | 'mock') {
      this.testType = type
      if (type === 'practice') {
        this.mode = 'practice'
        // Clear any leftover custom-test config/result from a previous
        // session so the Practice flow never gets mistaken for a custom test.
        this.customConfig = null
        this.customTestResult = null
      } else if (type === 'mock') {
        this.mode = 'test'
        this.customConfig = null
        this.customTestResult = null
      } else {
        // 'custom' — mode gets set later by setCustomConfig() once the user
        // finishes configuring subjects/duration/difficulty.
        this.mode = null
      }
    },
    setCustomConfig(config: CustomConfig, mode: PracticeMode = 'test') {
      this.customConfig = config
      this.mode = mode
    },
    clearCustomConfig() {
      this.customConfig = null
    },
    setCustomTestResult(result: CustomTestResult) {
      this.customTestResult = result
    },
    clearCustomTestResult() {
      this.customTestResult = null
    },
    setMockTest(test: MockTest) {
      this.mockTest = test
    },
    clearMockTest() {
      this.mockTest = null
    },
    reset() {
      this.exam = null
      this.examType = null
      this.testType = null
      this.subject = null
      this.scope = null
      this.chapter = null
      this.mode = null
      this.customConfig = null
      this.customTestResult = null
      this.mockTest = null
    },
  },
})