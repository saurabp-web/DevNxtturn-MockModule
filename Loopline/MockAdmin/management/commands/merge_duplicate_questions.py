"""
Place at: MockAdmin/management/commands/merge_duplicate_questions.py
(make sure management/ and management/commands/ both contain an __init__.py)

Usage:
  python manage.py merge_duplicate_questions            # dry run, only prints groups
  python manage.py merge_duplicate_questions --apply    # really merge

BACK UP THE DATABASE FIRST. Duplicates are grouped by content_hash (stem+options),
then by text_hash when the options are also (order-insensitively) similar.
The lowest question_id in a group is kept; the others are folded into it:
every appearance is copied over, related rows are re-pointed, then the extra
row is deleted.
"""
from collections import defaultdict
from difflib import SequenceMatcher

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError

from MockAdmin.models import Question, QuestionOption
from MockAdmin.views import _hash_norm, _numbers_signature, _specific_stem


def _opts(q):
    o = QuestionOption.objects.filter(question=q).first()
    return sorted(_hash_norm(getattr(o, f"option_{l}", "") or "") for l in "abcd") if o else []


def _same_options(a, b, min_ratio=0.85):
    if not a or not b or not any(a) or not any(b):
        return False
    return min(SequenceMatcher(None, x, y).ratio() for x, y in zip(a, b)) >= min_ratio


def _merge_appearances(master, other):
    apps = list(master.appearances or [])
    seen = {(a.get("exam_id"), a.get("year"), a.get("session") or "",
             a.get("paper") or "", a.get("mock_exam_id")) for a in apps}
    for a in (other.appearances or []):
        key = (a.get("exam_id"), a.get("year"), a.get("session") or "",
               a.get("paper") or "", a.get("mock_exam_id"))
        if key not in seen:
            apps.append(a)
            seen.add(key)
    master.appearances = apps
    master.is_previousyear = master.is_previousyear or other.is_previousyear
    master.is_practice = master.is_practice or other.is_practice
    master.is_custom = master.is_custom or other.is_custom
    master.is_mock = master.is_mock or other.is_mock
    if not master.mock_exam_id and other.mock_exam_id:
        master.mock_exam_id = other.mock_exam_id
    master.save()


def _repoint(master, other):
    """Move every row that points at `other` over to `master` (keeps master's own
    options / answer / solution when a one-to-one clash happens)."""
    for rel in Question._meta.related_objects:
        model, field = rel.related_model, rel.field.name
        for obj in model.objects.filter(**{field: other}):
            try:
                with transaction.atomic():
                    setattr(obj, field, master)
                    obj.save()
            except IntegrityError:
                obj.delete()          # master already has its own copy


class Command(BaseCommand):
    help = "Fold duplicate questions into one row that lists every exam/year it appeared in."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *a, **o):
        rows = list(Question.objects.filter(is_active=True).exclude(text_hash="").order_by("pk"))
        by_content, by_text = defaultdict(list), defaultdict(list)
        for r in rows:
            if r.content_hash:
                by_content[r.content_hash].append(r)
            by_text[r.text_hash].append(r)

        groups, used = [], set()
        for grp in by_content.values():
            if len(grp) > 1:
                groups.append(grp); used.update(x.pk for x in grp)
        for grp in by_text.values():
            grp = [x for x in grp if x.pk not in used]
            if len(grp) < 2:
                continue
            master = grp[0]; cluster = [master]; mo = _opts(master)
            for x in grp[1:]:
                if _same_options(mo, _opts(x)):
                    cluster.append(x)
            if len(cluster) > 1:
                groups.append(cluster)

        # Pass 3: reworded repeats (e.g. 'reacting with' vs 'reacting it with').
        # Bucketed by the first 12 letters of the stem so it stays fast.
        grouped = {x.pk for g in groups for x in g}
        buckets = defaultdict(list)
        for r in rows:
            if r.pk in grouped:
                continue
            buckets[_hash_norm(r.question_text)[:12]].append(r)
        for bucket in buckets.values():
            taken = set()
            for i, m in enumerate(bucket):
                if m.pk in taken or len(_hash_norm(m.question_text)) < 25:
                    continue
                ms, mn, mo = _hash_norm(m.question_text), _numbers_signature(m.question_text), _opts(m)
                cluster = [m]
                for x in bucket[i + 1:]:
                    if x.pk in taken:
                        continue
                    if (SequenceMatcher(None, ms, _hash_norm(x.question_text)).ratio() >= 0.92
                            and _numbers_signature(x.question_text) == mn
                            and (_same_options(mo, _opts(x)) or _specific_stem(m.question_text))):
                        cluster.append(x); taken.add(x.pk)
                if len(cluster) > 1:
                    groups.append(cluster); taken.add(m.pk)

        merged = 0
        for grp in groups:
            master, extras = grp[0], grp[1:]
            self.stdout.write(f"keep Q{master.pk}, fold {[x.pk for x in extras]}: "
                              f"{master.question_text[:70]!r}")
            if o["apply"]:
                with transaction.atomic():
                    for x in extras:
                        _merge_appearances(master, x)
                        _repoint(master, x)
                        x.delete()
                        merged += 1
        self.stdout.write(self.style.SUCCESS(
            f"{len(groups)} duplicate groups; {merged} rows merged" if o["apply"]
            else f"{len(groups)} duplicate groups found (dry run, nothing changed)"))