import { http } from './http'
import type { ExamWizardForm } from '@/types/exam'

/**
 * Flattens the wizard's nested `form` object into the payload
 * ExamCreateUpdateSerializer expects — now backed by real related tables
 * (ExamDetail, ExamPattern/ExamPatternSection, ExamBoard,
 * ExamImportantDate, ExamEligibility) instead of a JSON blob, so the
 * nesting here mirrors those tables directly.
 *
 * Two things intentionally do NOT make it into this payload yet:
 *  - form.basicInfo.examLogo / bannerImage are File objects. The Exam
 *    model's `logo` field is a URLField, so these need to go through a
 *    separate upload endpoint (or S3 presigned URL) first, then only the
 *    resulting URL gets sent here. Wire that once a media/upload endpoint
 *    exists — for now logo upload is a no-op.
 *  - classification.examCategory / conductingBody as free-text strings
 *    won't match a real PK once/if exam-categories get their own endpoint.
 */
export function mapWizardFormToPayload(form: ExamWizardForm, publish: boolean) {
  return {
    status: publish ? 'published' : 'draft',

    // basicInfo
    exam_name: form.basicInfo.examName,
    exam_code: form.basicInfo.shortName,
    description: form.basicInfo.description,
    conducting_body: form.classification.conductingBody,
    // logo: <URL from upload endpoint, once that exists>

    // classification — numeric PKs, since StepClassification.vue now
    // populates these from fetchExamTypes()/fetchExamLevels()
    exam_type: form.classification.examType || null,
    level: form.classification.examLevel || null,

    // academicMapping — numeric PKs from StepAcademicMapping.vue
    education_levels: form.academicMapping.educationLevel
      ? [form.academicMapping.educationLevel]
      : [],
    streams: form.academicMapping.stream ? [form.academicMapping.stream] : [],
    field: form.academicMapping.field || null,
    sub_field: form.academicMapping.subField || null,
    board: null,
    state: null,

    // examDetails -> ExamDetail (one-to-one)
    detail: {
      age_limit: form.examDetails.ageLimit,
      application_mode: form.examDetails.applicationMode,
      exam_mode: form.examDetails.examMode,
      exam_frequency: form.examDetails.examFrequency,
      duration: form.examDetails.duration,
      total_marks: form.examDetails.totalMarks ? Number(form.examDetails.totalMarks) : null,
      negative_marking: form.examDetails.negativeMarking,
      official_website: form.examDetails.officialWebsite,
      helpline_contact: form.examDetails.helplineContact,
    },

    // examPattern -> ExamPattern + ExamPatternSection[]
    pattern: {
      negative_marking: form.examPattern.negativeMarking,
      marking_scheme: form.examPattern.markingScheme,
      unattempted: form.examPattern.unattempted,
      sections: (form.examPattern.sections || []).map((s: any, i: number) => ({
        section_name: s.name,
        questions: Number(s.questions) || 0,
        marks: Number(s.marks) || 0,
        duration: s.duration,
        section_order: i + 1,
      })),
    },

    // examBoards -> ExamBoard[]
    exam_boards: (form.examBoards || []).map((b: any) => ({
      board_name: b.name,
      applicable_region: b.region,
      status: b.status,
    })),

    // importantDates -> ExamImportantDate (one-to-one)
    important_dates: {
      application_start: form.importantDates.applicationStart || null,
      application_end: form.importantDates.applicationEnd || null,
      admit_card_release: form.importantDates.admitCardRelease || null,
      exam_date: form.importantDates.examDate || null,
      result_date: form.importantDates.resultDate || null,
    },

    // eligibility -> ExamEligibility (one-to-one)
    eligibility_detail: {
      educational_qualification: form.eligibility.educationalQualification,
      minimum_marks: form.eligibility.minimumMarks,
      age_criteria: form.eligibility.ageCriteria,
      other_conditions: form.eligibility.otherConditions,
    },

    // syllabus: Subject -> Chapter -> Topic (real tables)
    syllabus: form.syllabus.map((subj: any) => ({
      subject_name: subj.subject,
      chapters: (subj.chapters || []).map((ch: any, ci: number) => ({
        chapter_name: ch.name,
        chapter_order: ci + 1,
        topics: (ch.topics || []).map((t: string, ti: number) => ({
          topic_name: t,
          topic_order: ti + 1,
        })),
      })),
    })),
  }
}

export async function createExam(form: ExamWizardForm, publish: boolean) {
  const payload = mapWizardFormToPayload(form, publish)
  const { data } = await http.post('/exams/', payload)
  return data
}

export async function updateExam(examId: number, form: ExamWizardForm, publish: boolean) {
  const payload = mapWizardFormToPayload(form, publish)
  const { data } = await http.put(`/exams/${examId}/`, payload)
  return data
}

export async function fetchExam(examId: number) {
  const { data } = await http.get(`/exams/${examId}/`)
  return data
}