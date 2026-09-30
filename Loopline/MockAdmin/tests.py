from unittest.mock import patch, MagicMock
from django.test import TestCase
from MockAdmin.models import (
    Exam, Subject, Chapter, Question, QuestionChapterMapping,
)
from MockAdmin.views import (
    _parse_ai_chapter_response,
    _ai_map_questions_batch,
    _save_questions_to_bank,
)


class AIChapterMappingTestCase(TestCase):
    def test_parse_ai_chapter_response(self):
        valid_ids = {10, 20, 30}
        raw_text = """
        Q1: 10
        Q2: 20
        Q3: 999  # hallucinated ID
        Q4: 0    # unclear
        Q5: 30
        """
        parsed = _parse_ai_chapter_response(raw_text, valid_ids)
        self.assertEqual(parsed.get(0), 10)
        self.assertEqual(parsed.get(1), 20)
        self.assertNotIn(2, parsed)  # 999 rejected
        self.assertEqual(parsed.get(3), 0)
        self.assertEqual(parsed.get(4), 30)

    @patch("MockAdmin.views.requests.post")
    def test_ai_map_questions_batch(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Q1: 101\nQ2: 102"}}]
        }
        mock_post.return_value = mock_response

        chapters = [(101, "Kinematics"), (102, "Thermodynamics")]
        questions = [
            {"question_text": "Calculate the acceleration of the projectile."},
            {"question_text": "Find the work done in isothermal expansion."},
        ]

        with patch("MockAdmin.views.settings.OPENROUTER_API_KEY", "test-key"):
            results = _ai_map_questions_batch("Physics", "JEE Main", chapters, questions)

        self.assertEqual(results.get(0), 101)
        self.assertEqual(results.get(1), 102)


class QuestionBankMultiMappingTestCase(TestCase):
    def setUp(self):
        self.exam_jee = Exam.objects.create(
            exam_name="JEE Main",
            exam_code="JEE_MAIN_TEST",
        )
        self.subject_jee = Subject.objects.create(exam=self.exam_jee, subject_name="Physics")
        self.chapter_jee = Chapter.objects.create(subject=self.subject_jee, chapter_name="Laws of Motion")

        self.exam_neet = Exam.objects.create(
            exam_name="NEET",
            exam_code="NEET_TEST",
        )
        self.subject_neet = Subject.objects.create(exam=self.exam_neet, subject_name="Physics")
        self.chapter_neet = Chapter.objects.create(subject=self.subject_neet, chapter_name="Newton's Laws")

    def test_question_deduplication_and_multi_chapter_mapping(self):
        q_text = "A body of mass 5 kg is acted upon by two perpendicular forces of 8 N and 6 N."

        # Import 1: JEE Main
        entries_jee = [{
            "question_text": q_text,
            "question_type": "MCQ",
            "marks": 4.0,
            "negative_marks": 1.0,
            "chapter_id": self.chapter_jee.chapter_id,
            "option_a": "2 m/s^2",
            "option_b": "4 m/s^2",
            "option_c": "6 m/s^2",
            "option_d": "8 m/s^2",
            "correct_answer": "A",
            "mapping_source": "ai",
            "mapping_confidence": 85,
        }]

        rows1, created1, reused1 = _save_questions_to_bank(self.exam_jee, entries_jee, {})
        self.assertEqual(created1, 1)
        self.assertEqual(reused1, 0)
        self.assertEqual(Question.objects.count(), 1)

        saved_q = rows1[0]
        # Verify primary mapping
        mappings = QuestionChapterMapping.objects.filter(question=saved_q)
        self.assertEqual(mappings.count(), 1)
        m1 = mappings.first()
        self.assertEqual(m1.chapter, self.chapter_jee)
        self.assertTrue(m1.is_primary)
        self.assertEqual(m1.source, "ai")

        # Import 2: Same question imported for NEET
        entries_neet = [{
            "question_text": q_text,
            "question_type": "MCQ",
            "marks": 4.0,
            "negative_marks": 1.0,
            "chapter_id": self.chapter_neet.chapter_id,
            "option_a": "2 m/s^2",
            "option_b": "4 m/s^2",
            "option_c": "6 m/s^2",
            "option_d": "8 m/s^2",
            "correct_answer": "A",
            "mapping_source": "ai",
            "mapping_confidence": 80,
        }]

        rows2, created2, reused2 = _save_questions_to_bank(self.exam_neet, entries_neet, {})
        # Question row must NOT be duplicated!
        self.assertEqual(created2, 0)
        self.assertEqual(reused2, 1)
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(rows2[0].pk, saved_q.pk)

        # But QuestionChapterMapping must now have 2 rows for this question!
        mappings_after = QuestionChapterMapping.objects.filter(question=saved_q).order_by("mapping_id")
        self.assertEqual(mappings_after.count(), 2)

        m_jee = mappings_after[0]
        m_neet = mappings_after[1]

        self.assertEqual(m_jee.chapter, self.chapter_jee)
        self.assertTrue(m_jee.is_primary)

        self.assertEqual(m_neet.chapter, self.chapter_neet)
        self.assertFalse(m_neet.is_primary)
        self.assertEqual(m_neet.source, "ai")
