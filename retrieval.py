"""Local RAG: simple intent rules, program aliases and a tiny BM25 index.

No paid embeddings, model download or external database is required.
Only knowledge.jsonl is factual evidence; question examples help routing.
"""
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


def normalize(text):
    text = text.lower().replace('&', ' and ')
    for pattern, replacement in [
        (r'\bbachelor of computer applications\b', 'bca'),
        (r'\bmaster of computer applications\b', 'mca'),
        (r'\bbachelor of technology\b', 'btech'),
        (r'\bmaster of technology\b', 'mtech'),
        (r'\bb\s*\.?\s*tech\b', 'btech'), (r'\bm\s*\.?\s*tech\b', 'mtech'),
        (r'\bb\.?\s*c\.?\s*a\b', 'bca'), (r'\bm\.?\s*c\.?\s*a\b', 'mca'),
        (r'\bcomputer science(?: and engineering)?\b', 'cse'),
        (r'\bartificial intelligence\b', 'ai'), (r'\buser experience\b', 'ux'),
        (r'\bfull[ -]?stack development\b', 'fullstack'),
        (r'\binternet of things\b', 'iot'),
        (r'\b(database management systems?|dbms)\b', 'dbms'),
        (r'\bvaishali\b', 'vishali'), (r'\breeshma\b', 'reshma'),
    ]:
        text = re.sub(pattern, replacement, text)
    return re.sub(r'[^a-z0-9@]+', ' ', text).strip()


STOP = set('a an the is are was were do does can could for to of in at on and or me my i you your we us it its this that what which how tell about please hai hain kya ka ki ke ko mein mujhe batao listed supplied dataset workbook data current confirmed confirm verified'.split())


def tokens(text):
    return [t for t in normalize(text).split() if t not in STOP]


class SearchIndex:
    """BM25 ranks word matches, giving uncommon words more weight."""
    def __init__(self, texts):
        self.documents = [Counter(tokens(t)) for t in texts]
        self.lengths = [sum(d.values()) for d in self.documents]
        self.average = sum(self.lengths) / max(len(texts), 1) or 1
        counts = Counter(t for d in self.documents for t in d)
        self.idf = {t: math.log(1 + (len(texts)-n+0.5)/(n+0.5)) for t, n in counts.items()}

    def rank(self, query):
        words = set(tokens(query))
        scores = []
        for i, doc in enumerate(self.documents):
            score = sum(self.idf.get(t, 0) * doc[t] * 2.2 /
                        (doc[t] + 1.2 * (0.25 + 0.75*self.lengths[i]/self.average))
                        for t in words if doc[t])
            if score:
                scores.append((score, i))
        return sorted(scores, reverse=True)


# Ordered rules resolve overlapping topics before generic word matching.
RULES = [
 ('contact', r'(email|contact|phone).*(refund grievances)|refund grievances.*(email|contact)'),
 ('accreditation', r'accredit|approval documents|program.*approval'),
 ('application_status', r'(my|mera|meri|personal).*(application|admission).*(status|accepted)|applicant dashboard|application number|application status'),
 ('fee_due_date', r'outstanding|pending fee|payment deadline|fee.*(due|calendar)|semester fee.*deadline'),
 ('timetable', r'timetable|class.*(time|baje)|kal meri|exam.*schedule'),
 ('refund', r'refund|withdraw|cancellation|cancel.*admission|get back.*(day|deadline)'),
 ('mess_fee', r'\bmess\b|meal plan'),
 ('hostel_facilities', r'laundry|housekeeping|pool|hostel.*(facilit|wifi|wi fi|gym)'),
 ('hostel_optional', r'(hostel.*(compulsory|mandatory|optional))|(optional|compulsory|mandatory).*hostel|day scholar'),
 ('hostel_fee', r'hostel|occupancy|ac room|non ac|accommodation'),
 ('fee_installments', r'installment|instalment'),
 ('scholarship_process', r'scholarship.*(apply|application|renew|deadline|combine|stack)|apply.*scholarship|scholarships ko combine'),
 ('scholarship', r'scholarship|waiver|sports.*(gold|silver|bronze)|financial assistance'),
 ('campus_visit', r'campus.*(visit|tour)|visit.*campus|guided tour'),
 ('transport', r'bus|transport|pickup|pick up'),
 ('placement', r'placement|package|recruiter|graduating batch|average salary'),
 ('live_seats', r'(seat.*(available|availability|remain|vacant))|vacant.*seat'),
 ('live_admission', r'admission.*(open|today|extension)|still apply|after the deadline|next admission cycle|admission cycle|next.*intake'),
 ('seat_booking', r'seat booking|booking amount|booking deadline|pal issuance'),
 ('admission_dates', r'deadline|application window|application.*(start|begin)|admission date|application date'),
 ('documents', r'document|marksheet|mark sheet|identity|photograph|\bupload\b'),
 ('eligibility', r'eligib|prerequisite|without math|maths ke bina|qualifying subjects|50 percent|scored.*percent'),
 ('entrance_selection', r'entrance|jluet|interview|selection'),
 ('admission_confirmation', r'provisional|original.*verification|admission.*final|final.*admission|registration.*condition'),
 ('seat_booking', r'seat booking|booking amount|booking deadline|pal issuance'),
 ('application_portal', r'application.*(portal|address)|apply online|form ka.*portal'),
 ('application_fee', r'application.*(fee|charge)|form.*fee'),
 ('application_process', r'(apply|application|admission|form).*(step|process|submit|kaise)|how.*apply|after completing.*application'),
 ('education_loan', r'education loan|lender|loan.*(approv|guidance|guarantee)'),
 ('program_transfer', r'(change|changing|transfer|move|switch).*(program|bca|btech)|program.*(change|transfer)'),
 ('medium_instruction', r'medium.*instruction|teaching language|language policy|english.*teach'),
 ('accreditation', r'accredit|approval|recognition'),
 ('labs', r'\blab\b|\blabs\b|laborator|gpu'),
 ('faculty', r'\bemail\b|staff directory|faculty directory|contact.*(dr|anjali)|head of|heads fast|hod|professor'),
 ('faculty_assignment', r'who.*(teach|teacher)|teacher kaun|faculty course mapping|teach.*(semester|class)|faculty.*subject'),
 ('curriculum', r'credit|curriculum|syllabus|semester allocation|course code'),
 ('student_support', r'portal login|help desk|support.*(contact|desk)|examination office|course registration support|fee receipt'),
 ('contact', r'contact|phone|campus address|admissions.*email|address.*campus'),
 ('program_comparison', r'compare|comparison|choose|better|versus|\bvs\b|which.*program.*(me|child)|likes computers'),
 ('fee_breakdown', r'break.*down|breakdown|charges.*separate|total.*include.*admission|tuition.*total|charges.*annual total'),
 ('program_fee', r'fee|tuition|charges|yearly cost|annual cost|fees|cost'),
 ('program_duration', r'duration|how long|how many years|kitne saal'),
 ('program_status', r'(robotics|sustainable energy|iot|electronics|bca ai|bca artificial).*(offer|apply|available|confirmed)|currently offered'),
 ('program_info', r'program|degree|undergraduate options|course'),
 ('campus', r'library|campus|wifi|wi fi|security|books'),
]

TOPICS = {'program_duration': 'program_info', 'fee_breakdown': 'program_fee',
          'program_status': 'program_info'}
NO_DATA = {
 'refund': 'The refund figures need clarification, including the exact 15/30-day boundaries and caution-money treatment. I cannot calculate or promise a refund. Please confirm the applicable written policy with admissions.',
 'placement': 'A dated FAST program-level placement report is not connected. I cannot confirm placement percentages, packages or guaranteed jobs. Ask admissions for the program and graduating batch report.',
 'hostel_facilities': 'The dataset does not establish which hostel facilities are included, chargeable or currently available. Please confirm laundry, Wi-Fi, gym and other facilities with the hostel office.',
 'curriculum': 'An approved curriculum is not connected, so I cannot confirm official course codes, credits or semester allocations. Check the syllabus for your program, specialization and regulation year.',
 'student_support': 'Verified student-support office details and hours are not connected. Please check the official student portal or university directory for the relevant support office.',
 'program_status': 'That program appears only in a listing that still needs confirmation. I cannot confirm current availability or its fees. Please ask admissions for the current program list.',
}
NEED_PROGRAM = {'program_fee', 'fee_breakdown', 'program_duration'}
HARD_FACTS = {'program_fee', 'program_info', 'program_duration', 'faculty',
              'faculty_assignment', 'hostel_fee', 'scholarship', 'admission_dates',
              'contact', 'application_fee', 'eligibility', 'entrance_selection',
              'seat_booking', 'fee_breakdown'}
POLICY_ANSWERS = {
 'application_status': 'I cannot access your application account or personal admission status. Please use your applicant dashboard or confirm with admissions. Do not share your password here.',
 'mess_fee': 'A separate mess fee is not provided. The listed hostel room charge must not be treated as a mess-inclusive total. Please confirm meal charges with the hostel office.',
 'fee_due_date': 'Your personal balance and current fee payment calendar are not connected. Please check the official student portal or fee notice.',
 'timetable': 'A current timetable is not connected. Please check the official timetable for your program, semester and section; I cannot confirm class or exam times.',
 'live_seats': 'Live seat availability is not connected. Please confirm current vacancies for your selected program with admissions.',
 'program_comparison': 'Which programs are you comparing, and what are your interests and qualifying subjects? I can compare their listed duration and fees, but the dataset does not establish which has better learning outcomes or placements.',
 'scholarship_process': 'The data lists scholarship categories and rewards, but no complete application procedure, current deadline, stacking or renewal rules. Which scholarship category do you mean? Please confirm its current instructions with admissions.',
 'transport': 'Transport routes, stops, charges and pickup times are not connected. Please confirm availability for your locality with the university.',
 'labs': 'A verified FAST laboratory inventory is not connected. Please ask the university for the facilities and access rules for your program.',
 'accreditation': 'Program-specific approval or accreditation documents are not connected. Please confirm the current official approval for the program you are considering.',
 'live_admission': 'The supplied 2026–27 data lists a 31 August 2026 deadline. That date has passed. No current opening, extension or next-cycle dates are established, so please confirm the current admission window with admissions.',
}


@dataclass
class Result:
    intent: str
    records: list = field(default_factory=list)
    direct_answer: str = ''
    programs: list = field(default_factory=list)
    retrieval_ms: float = 0.0


class KnowledgeBase:
    def __init__(self, folder):
        folder = Path(folder)
        self.records = self._read(folder/'knowledge.jsonl')
        allowed = {'reported_unverified', 'user_confirmed', 'historical', 'policy', 'verified'}
        self.records = [r for r in self.records if r['evidence_status'] in allowed]
        if not self.records:
            raise ValueError('The knowledge file contains no permitted records.')
        self.by_topic = defaultdict(list)
        for r in self.records:
            self.by_topic[r['topic']].append(r)
        self.index = SearchIndex([' '.join(str(r.get(k, '')) for k in
            ['question','entity','keywords','answer']) for r in self.records])
        self.examples = self._read(folder/'intent_examples.jsonl')
        if any(q['split'] != 'development' for q in self.examples):
            raise ValueError('Evaluation questions must not enter the routing index.')
        self.example_index = SearchIndex([q['question'] for q in self.examples])
        self.programs = [r['entity'] for r in self.by_topic['program_info']]
        self.faculty = self._read(folder/'faculty_directory.jsonl')

    @staticmethod
    def _read(path):
        with path.open(encoding='utf-8') as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def resolve_programs(self, text):
        q = normalize(text)
        found = []
        for p in self.programs:
            words = normalize(p).split()
            family, details = words[0], words[1:]
            if family not in q.split():
                continue
            if family == 'mca' or all(d in q.split() for d in details):
                found.append(p)
        # A bare BCA must not silently become BCA General.
        return found

    def identify_intent(self, text):
        q = normalize(text)
        if re.search(r'\b(my|mine|mera|meri|mere|apna|atharva|aarna)\b', q) and re.search(r'\b(score|scores|marks|result|results|cgpa|sgpa|attendance)\b', q) and not (re.search(r'\b\d+(?:\.\d+)?\b', q) and re.search(r'eligib|scholarship|qualify', q)):
            return 'personal_records'
        if re.fullmatch(r'(score|scores|marks|result|results|cgpa|sgpa)[ ?.]*', q):
            return 'score_clarification'
        if re.search(r'\b(other|another|ather)\s+(school|college|university)\b', q):
            return 'out_of_scope'
        if re.fullmatch(r'(hi|hello|hey|namaste|good morning|good evening)[ !.]*', q):
            return 'greeting'
        if re.search(r'\b(goodbye|bye|see you|leaving now)\b', q):
            return 'goodbye'
        if re.search(r'^(thanks|thank you|shukriya)\b', q) and not re.search(r'\b(but|also|what|how|can|fee|hostel)\b', q):
            return 'thanks'
        if re.search(r'ignore.*(instruction|rule|prompt)|system prompt|pretend.*verified|invent.*(fee|email|fact)', q):
            return 'out_of_scope'
        if re.search(r'\b(recipe|cricket|football|weather|poem|movie|sorting program|normalization|write.*code|joke)\b', q):
            return 'out_of_scope'
        if re.search(r'^(hi|hello|namaste|good morning)\b', q) and not re.search(r'fee|apply|program|hostel|scholarship', q):
            return 'greeting'
        if re.search(r'\bf0\d{2}\b', q):
            return 'faculty'
        if re.search(r'who.*teach|teaches.*class|teacher kaun|faculty.*mapping', q):
            return 'faculty_assignment'
        if any((set(normalize(p['name']).split()) - {'dr','kumar','singh','sharma'}) & set(q.split()) for p in self.faculty):
            return 'faculty'
        for intent, pattern in RULES:
            if re.search(pattern, q):
                return intent
        # Word-search fallback supports paraphrases without a separate LLM call.
        ranked = self.example_index.rank(text)
        if ranked:
            score, idx = ranked[0]
            example = self.examples[idx]
            overlap = set(tokens(text)) & set(tokens(example['question']))
            if len(overlap) >= 2 and score >= 3:
                return example['intent']
        return 'ask_clarification'

    def retrieve(self, text, previous_programs=None, limit=6, previous_intent=''):
        from time import perf_counter
        start = perf_counter()
        result = self._retrieve(text, previous_programs or [], limit, previous_intent)
        result.retrieval_ms = (perf_counter()-start)*1000
        return result

    def _retrieve(self, text, previous_programs, limit, previous_intent):
        q = normalize(text)
        # Independently requested areas are answered together, not silently dropped.
        clauses = re.split(r'\s+(?:and|also|aur|plus)\s+', q)
        clause_intents = [self.identify_intent(c) for c in clauses]
        shared_hostel = 'hostel' in q and set(clause_intents) <= {'campus','hostel_facilities','hostel_fee','hostel_optional'}
        if 1 < len(clauses) <= 3 and not shared_hostel and 'ask_clarification' not in clause_intents and len(set(clause_intents))>1:
            context = self.resolve_programs(text) or previous_programs
            parts = [self._retrieve(c, context, limit, previous_intent) for c in clauses]
            evidence = {r['record_id']:r for part in parts for r in part.records}
            answer = '\n\n'.join('**'+part.intent.replace('_',' ').capitalize()+'**\n\n'+
                (part.direct_answer or self.format_answer(part.intent,part.records,c))
                for c,part in zip(clauses,parts))
            return Result('multiple_enquiries', list(evidence.values()), answer, context)
        intent = self.identify_intent(text)
        if intent == 'ask_clarification' and previous_intent in NEED_PROGRAM and re.search(r'\b(btech|mtech|bca|mca)\b', q):
            intent = previous_intent
        if intent == 'greeting':
            return Result(intent, direct_answer='Hello! I can help with FAST programs, listed fees, admission steps, scholarships, hostel information and faculty. What would you like to know?')
        if intent == 'thanks':
            return Result(intent, direct_answer='You’re welcome. Is there anything else you would like to know about FAST?')
        if intent == 'goodbye':
            return Result(intent, direct_answer='Goodbye! Please confirm current admission details with the university before applying.')
        if intent == 'personal_records':
            return Result(intent, direct_answer="I couldn’t find this information in our database. Your personal marks, results, CGPA and attendance are not connected to FAST_CHATBOT. Please check your student ERP or contact the university.\n\nI can help explain admission requirements and scholarship criteria, but I can’t view your student account. Please don’t share your password here.")
        if intent == 'score_clarification':
            return Result(intent, direct_answer="Which score do you mean?\n\n- **Entrance or admission marks**\n- **Qualifying marks for eligibility or scholarships**\n- **Your personal semester marks, CGPA or results**\n\nTell me the score type and course. Personal results are not available in this chatbot’s database; please check your student ERP.")
        if intent == 'out_of_scope':
            return Result(intent, direct_answer="I can help with information about the Faculty of Science & Technology (FAST) at Jagran Lakecity University. I couldn’t find this information in our database.\n\nYou can ask me about **courses and duration, fees, admissions and documents, scholarships, hostel information, or faculty contacts**.\n\nFor example: ‘What are the B.Tech CSE fees?’ or ‘How do I apply?’")
        if intent == 'ask_clarification':
            return Result(intent, direct_answer="I couldn’t find information matching your question in our database. Could you rephrase it or choose a topic below?\n\nWhich FAST information do you need: **programs, fees, admissions, scholarships, hostel or faculty**?")
        if intent in NO_DATA:
            return Result(intent, direct_answer=NO_DATA[intent])
        topic = TOPICS.get(intent, intent)
        programs = self.resolve_programs(text)
        explicit_family = bool(re.search(r'\b(btech|mtech|bca|mca)\b', q))
        # Never carry an old program into a request naming a new, unresolved one.
        if not programs and not explicit_family and re.search(r'\b(its|it|that|same|uska|uski|iska|iski|fees|fee|duration)\b', q):
            programs = previous_programs
        unsupported_program = bool(re.search(r'\b(robotics|iot|sustainable energy|electronics)\b', q) or re.search(r'bca ai|btech data science', q))
        if intent in NEED_PROGRAM and unsupported_program:
            return Result(intent, direct_answer=NO_DATA['program_status'])
        if intent in NEED_PROGRAM:
            years = set(re.findall(r'\b20\d{2}\b', text))
            if years and not years <= {'2026','2027'}:
                return Result(intent, direct_answer='Only the supplied 2026–27 fee/program records are connected. I cannot confirm amounts or rules for the requested academic year.')
            if '2027' in years and not re.search(r'2026\s*[-–/]\s*(27|2027)', text):
                return Result(intent, direct_answer='Only the supplied 2026–27 records are connected. Fees and admission details for 2027–28 are not available.')
            families = set(re.findall(r'\b(btech|mtech|bca|mca)\b', q))
            resolved = {normalize(p).split()[0] for p in programs}
            if families - resolved:
                return Result(intent, direct_answer='Please specify the specialization for each program, for example B.Tech CSE or BCA General. I will not assume a fee for an unspecified specialization.')
        if intent in NEED_PROGRAM and not programs:
            return Result(intent, direct_answer='Which program do you mean? Please name the degree and specialization, for example B.Tech CSE, B.Tech AI, BCA General or MCA.')
        candidates = list(self.by_topic.get(topic, []))
        if programs and topic in {'program_info', 'program_fee'}:
            candidates = [r for r in candidates if r['entity'] in programs]
        elif topic in {'program_info', 'program_fee'} and explicit_family:
            families = set(re.findall(r'\b(btech|mtech|bca|mca)\b', q))
            candidates = [r for r in candidates if normalize(r['entity']).split()[0] in families]
        if intent == 'faculty':
            names = []
            for p in self.faculty:
                meaningful = set(normalize(p['name']).split()) - {'dr','kumar','singh','sharma'}
                if meaningful & set(q.split()) or p['faculty_id'].lower() in q.split():
                    names.append(p['name'])
            if names:
                candidates = [r for r in candidates if r['entity'] in names]
            elif re.search(r'head|hod', q):
                candidates = [r for r in candidates if 'F001' in r['answer']]
            elif not re.search(r'list|directory|all|faculty', q):
                return Result(intent, direct_answer='Which faculty member do you mean? Please give their name or faculty ID.')
        if intent == 'faculty_assignment':
            ids = [p['faculty_id'] for p in self.faculty if
                (set(normalize(p['name']).split()) - {'dr','kumar','singh','sharma'}) & set(q.split())]
            if ids:
                candidates = [r for r in candidates if r['entity'] in ids]
        if intent == 'documents':
            applicant = 'PG' if re.search(r'\b(pg|postgraduate|graduation|mca|mtech)\b', q) else ('UG' if re.search(r'\b(ug|undergraduate|btech|bca|class 12)\b', q) else None)
            if applicant:
                groups = {applicant,'All'} | ({'International','International Document'} if 'international' in q else set())
                candidates = [r for r in candidates if r['entity'] in groups]
            elif not re.search(r'aadhaar|apaar|passport|photograph|signature|international',q):
                return Result(intent, direct_answer='Are you applying for an undergraduate (UG) or postgraduate (PG) program? The document checklist depends on your applicant type.')
        if intent == 'eligibility':
            if re.search(r'\b(btech|bca|ug|undergraduate|class 12)\b',q):
                candidates = [r for r in candidates if r['entity']!='Pg Eligibility']
            if re.search(r'\b(mtech|mca|pg|postgraduate|graduation)\b',q):
                candidates = [r for r in candidates if r['entity']!='Ug Eligibility']
        if intent == 'scholarship':
            if not re.search(r'academic|sports|financial|international|national|state|gold|silver|bronze|participation|tuition|waiver',q):
                return Result(intent, direct_answer='The supplied data lists academic scholarships, sports scholarships and financial assistance. Which category would you like to explore? Awards and current eligibility must be confirmed with the university.')
            for term in ['academic','sports','financial assistance','international','national','state','gold','silver','bronze','participation']:
                if re.search(r'\b'+term+r'\b', q):
                    candidates = [r for r in candidates if re.search(r'\b'+term+r'\b', normalize(r['answer']))]
        if intent == 'hostel_fee':
            for term in ['single','double','triple','ensuite']:
                if term in q.split():
                    candidates = [r for r in candidates if term in normalize(r['entity']).split()]
            if 'non ac' in q:
                candidates = [r for r in candidates if 'non ac' in normalize(r['entity'])]
            elif 'ac' in q.split():
                candidates = [r for r in candidates if 'non ac' not in normalize(r['entity'])]
        ranking = {self.records[i]['record_id']: score for score, i in self.index.rank(text)}
        candidates.sort(key=lambda r: ranking.get(r['record_id'], 0), reverse=True)
        if intent == 'faculty':
            # Project owner's requested directory order; IDs remain unchanged.
            faculty_order = [
                'F001', 'F002', 'F003', 'F004', 'F007', 'F006', 'F005',
                'F008', 'F009', 'F010', 'F011', 'F012', 'F013', 'F014',
            ]
            positions = {fid: i for i, fid in enumerate(faculty_order)}
            name_to_id = {p['name']: p['faculty_id'] for p in self.faculty}
            candidates.sort(
                key=lambda r: positions.get(name_to_id.get(r['entity']), 999)
            )
        if intent=='faculty_assignment':
            candidates = [r for r in candidates if ranking.get(r['record_id'], 0)>0]
        # Complete overview lists remain compact; ordinary questions use top-k.
        overview = intent in {'program_info','faculty'} and re.search(r'list|directory|all|which programs|degree programs|undergraduate options', q)
        chosen = candidates if overview else candidates[:limit]
        if not chosen:
            return Result(intent, direct_answer='That information is not available in the connected dataset. Please confirm it with the relevant university office.', programs=programs)
        if intent in POLICY_ANSWERS:
            return Result(intent, chosen, POLICY_ANSWERS[intent], programs)
        if intent in HARD_FACTS or all(r['evidence_status']=='policy' for r in chosen):
            return Result(intent, chosen, self.format_answer(intent, chosen, text), programs)
        return Result(intent, chosen, programs=programs)

    @staticmethod
    def format_answer(intent, records, question=''):
        # No generated numbers or guessed contacts enter these answers.
        if intent in {'program_info','program_duration'}:
            body='\n\n'.join(r['answer'] for r in records)
        elif intent in {'faculty','faculty_assignment'}:
            body='\n\n'.join(r['answer'] for r in records)
            body+='\n\nSource: the final faculty table supplied for this project. General subject allocations do not establish the current class timetable.'
        else:
            body='\n\n'.join(r['answer'] for r in records)
        if any(r['evidence_status']=='reported_unverified' for r in records):
            body+='\n\nThese are supplied 2026–27 records. Please confirm current applicability with the university.'
        if intent == 'eligibility':
            body+='\n\nGeneral thresholds do not establish your program-specific eligibility. Which program and qualifying subjects do you have?'
        if intent == 'entrance_selection':
            body+='\n\nThe dataset does not establish a definitive FAST program-specific entrance rule. Law and Design rules must not be applied to FAST by inference.'
        if intent == 'admission_dates':
            body+='\n\nThese are historical dates. The recorded 31 August 2026 deadline has passed; no current opening or extension is established.'
        return body
