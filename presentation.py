"""Presentation transforms evidence into readable text; never derives new official fees."""
import re

NOTICE = 'These are supplied 2026–27 records. Please confirm current applicability with the university.'


def display_answer(answer: str, intent: str, records: list) -> str:
    # Dataset disclaimer is rendered in the persistent UI; retain all specific caveats.
    answer = answer.replace('\n\n' + NOTICE, '').replace(NOTICE, '').strip()
    if intent not in {'program_fee', 'fee_breakdown'} or len(records) != 1:
        return answer
    record = records[0]
    raw = record.get('answer', '')
    # Only present existing supplied amounts, never compute an unsupported total.
    fields = (
        ('Resource fee', r'\bresource fee\s*(?:INR|Rs\.?|₹)\s*([\d,]+)'),
        ('Tuition fee', r'\btuition\s*(?:fee)?\s*(?:INR|Rs\.?|₹)\s*([\d,]+)'),
        ('Examination fee', r'\bexamination fee\s*(?:INR|Rs\.?|₹)\s*([\d,]+)'),
        ('Listed annual total', r'\b(?:listed\s+)?annual total\s*[:]?\s*(?:INR|Rs\.?|₹)\s*([\d,]+)'),
        ('Admission charges (separate)', r'\badmission charges\s*(?:INR|Rs\.?|₹)\s*([\d,]+)'),
        ('Caution money (separate)', r'\bcaution money\s*(?:INR|Rs\.?|₹)\s*([\d,]+)'),
    )
    amounts = [(name, re.search(pattern, raw, flags=re.I)) for name, pattern in fields]
    if not all(m for _, m in amounts):
        return answer
    heading = record.get('entity', 'Program')
    rows = ['### ' + heading + ' — listed fees (2026–27)', '', '| Fee component | Amount |', '|---|---:|']
    def indian_currency(raw):
        digits = str(int(raw.rstrip(',').replace(',', '')))
        if len(digits) <= 3:
            return digits
        tail = digits[-3:]
        head = digits[:-3]
        groups = []
        while head:
            groups.insert(0, head[-2:])
            head = head[:-2]
        return ','.join(groups + [tail])
    rows += [f'| {name} | ₹{indian_currency(m.group(1))} |' for name, m in amounts]
    rows += ['', '**Important:** Admission charges and caution money are separate from the listed annual total. Their payment frequency and refund conditions require confirmation. Hostel and mess are excluded from this academic-fee record.']
    return '\n'.join(rows)
