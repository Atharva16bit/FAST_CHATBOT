"""Small display helpers; original evidence stays unchanged for retrieval."""
import re


def clean_answer(text):
    """Hide internal citations and repeated boilerplate, keeping factual limits."""
    text = re.sub(r'\[KB\d+(?:\s*,\s*KB\d+)*\]', '', text)
    text = text.replace('These are supplied 2026–27 records. Please confirm current applicability with the university.', '')
    text = text.replace('Source: the final faculty table supplied for this project. General subject allocations do not establish the current class timetable.', '')
    text = text.replace('The supplied workbook lists ', '')
    text = re.sub(r' +([.,;:])', r'\1', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def fee_answer(result):
    """Format stored fee components without inventing or calculating a bill."""
    if result.intent not in {'program_fee', 'fee_breakdown'} or not result.records:
        return ''
    sections = []
    for record in result.records:
        if record['topic'] != 'program_fee':
            return ''
        amounts = re.findall(r'INR (\d(?:[\d,]*\d)?)', record['answer'])
        if len(amounts) != 6:
            return ''  # Preserve the original answer if its schema changes.
        resource, tuition, exam, total, admission, caution = amounts
        sections.append(
            f"### {record['entity']}\n\n"
            f"**Annual academic fee: ₹{total}** · {record['academic_year']}\n\n"
            '| Component | Annual amount |\n| --- | ---: |\n'
            f'| Tuition | ₹{tuition} |\n| Resource fee | ₹{resource} |\n'
            f'| Examination fee | ₹{exam} |\n| **Total** | **₹{total}** |\n\n'
            f'Additional listed charges: admission ₹{admission}; caution money ₹{caution}. '
            'These are separate from the annual total. Confirm their payment frequency '
            'and refund conditions with admissions. Hostel and mess are extra.'
        )
    return '\n\n'.join(sections)
