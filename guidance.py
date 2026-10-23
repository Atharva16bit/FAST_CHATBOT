"""Local recovery choices; these do not search or access external accounts."""
from urllib.parse import urlsplit

TOPIC_CHOICES = [
    ('Programs', 'Which programs are listed under FAST?'),
    ('Fees', None),
    ('Admissions', 'How do I apply for admission?'),
    ('Scholarships', 'Which scholarship categories are available?'),
    ('Hostel', 'What hostel room fees are listed?'),
    ('Faculty', 'List the faculty directory.'),
]

SCORE_CHOICES = [
    ('Admission eligibility', 'What are the admission eligibility requirements?'),
    ('Entrance requirements', 'What entrance selection requirements are listed?'),
    ('Scholarship marks', 'What academic scholarship bands are listed?'),
    ('My semester results', 'Where can I check my semester results?'),
]


def needs_guidance(message):
    intent = message.get('intent', '')
    if intent in {'ask_clarification', 'out_of_scope', 'personal_records', 'score_clarification'}:
        return True
    if intent in {'greeting', 'thanks', 'goodbye', 'program_fee', 'fee_breakdown', 'program_duration'}:
        return False
    # Missing-information replies may have no records or only coverage notes.
    records = message.get('sources', [])
    return bool(intent) and (not records or all(r.get('evidence_status') == 'policy' for r in records))


def erp_link(value):
    """Only use an explicitly configured HTTPS portal link."""
    value = value.strip()
    try:
        parsed = urlsplit(value)
        if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
            return value
    except ValueError:
        pass
    return ''
