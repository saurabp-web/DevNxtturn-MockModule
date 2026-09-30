import { http } from './http'

// All of these already exist on the backend (urls.py) and were previously
// unused by the wizard — StepClassification.vue and StepAcademicMapping.vue
// had hardcoded <option> lists. This file wires them to the real endpoints.

export interface Option {
  id: number
  name: string
}

// NOTE: adjust the field names below (`type_name`, `level_name`, etc.) to
// match whatever the *ListView serializers actually return — inspect one
// response in the network tab and tweak the `map()` calls if they differ.

export async function fetchExamTypes(): Promise<Option[]> {
  const { data } = await http.get('/filters/exam-types/')
  return data.map((d: any) => ({ id: d.exam_type_id, name: d.type_name }))
}

// CHANGED: now accepts an optional examTypeId so Academic Mapping's
// Education Level dropdown can be filtered to only levels actually used
// by exams of the selected exam type (backend already supported this
// via ?exam_type_id=, it just wasn't being passed from the frontend).
export async function fetchEducationLevels(examTypeId?: number | string): Promise<Option[]> {
  const { data } = await http.get('/filters/education-levels/', {
    params: examTypeId ? { exam_type_id: examTypeId } : {},
  })
  return data.map((d: any) => ({ id: d.education_level_id, name: d.education_level }))
}

// CHANGED: now accepts an optional educationLevelId (in addition to the
// existing examTypeId) so Stream can cascade off the selected Education
// Level, not just Exam Type. Backend: StreamListView now supports both
// ?exam_type_id= and ?education_level_id=, combinable.
export async function fetchStreams(
  examTypeId?: number | string,
  educationLevelId?: number | string,
): Promise<Option[]> {
  const params: Record<string, number | string> = {}
  if (examTypeId) params.exam_type_id = examTypeId
  if (educationLevelId) params.education_level_id = educationLevelId
  const { data } = await http.get('/filters/streams/', { params })
  return data.map((d: any) => ({ id: d.stream_id, name: d.stream_name }))
}

// CHANGED: now accepts an optional streamId so Field cascades off the
// selected Stream (backend already supported ?stream_id=, it just
// wasn't being passed from the frontend).
export async function fetchFields(streamId?: number | string): Promise<Option[]> {
  const { data } = await http.get('/filters/fields/', {
    params: streamId ? { stream_id: streamId } : {},
  })
  return data.map((d: any) => ({ id: d.field_id, name: d.field_name }))
}

export async function fetchSubFields(fieldId?: number): Promise<Option[]> {
  const { data } = await http.get('/filters/sub-fields/', {
    params: fieldId ? { field: fieldId } : {},
  })
  return data.map((d: any) => ({ id: d.sub_field_id, name: d.sub_field_name }))
}

export async function fetchBoards(): Promise<Option[]> {
  const { data } = await http.get('/filters/boards/')
  return data.map((d: any) => ({ id: d.board_id, name: d.board_name }))
}

export async function fetchStates(): Promise<Option[]> {
  const { data } = await http.get('/filters/states/')
  return data.map((d: any) => ({ id: d.state_id, name: d.state_name }))
}

export async function fetchExamLevels(): Promise<Option[]> {
  const { data } = await http.get('/filters/exam-levels/')
  return data.map((d: any) => ({ id: d.level_id, name: d.level_name }))
}

// NOTE: unlike everything above, these two are NOT under /api/filters/ —
// they're /api/subjects/ and /api/chapters/, and the response is a
// wrapped object ({exam_id, count, subjects}), not a flat array. Also,
// SubjectListView requires exam_id (subjects belong to an existing Exam
// row, not a global catalog) — this only works once the exam being
// created already has an id. If the wizard doesn't create a draft Exam
// until Publish, this endpoint can't be called from Step 3 as-is.
export async function fetchSubjects(examId: number | string): Promise<Option[]> {
  const { data } = await http.get('/subjects/', { params: { exam_id: examId } })
  return data.subjects.map((d: any) => ({ id: d.id, name: d.label }))
}

export async function fetchChapters(subjectId: number | string): Promise<Option[]> {
  const { data } = await http.get('/chapters/', { params: { subject_id: subjectId } })
  return data.chapters.map((d: any) => ({ id: d.id, name: d.label }))
}