"""Local routing/latency regression report. No Gemini calls or API key needed."""
import json
import statistics
import time
from pathlib import Path
from retrieval import KnowledgeBase

ROOT=Path(__file__).resolve().parent

def main():
    start=time.perf_counter()
    kb=KnowledgeBase(ROOT/'data')
    index_ms=(time.perf_counter()-start)*1000
    questions=[json.loads(line) for line in (ROOT/'evaluation/questions.jsonl').read_text().splitlines()]
    results=[]
    for question in questions:
        answer=kb.retrieve(question['question'])
        results.append({'question_id':question['question_id'],'question':question['question'],
            'expected_intent':question['intent'],'actual_intent':answer.intent,
            'match':answer.intent==question['intent'],'records':len(answer.records)})
    latencies=[]
    for _ in range(10):
        for question in questions:
            latencies.append(kb.retrieve(question['question']).retrieval_ms)
    latencies.sort()
    report={
        'dataset_records':len(kb.records),'routing_examples':len(kb.examples),
        'regression_questions':len(results),'intent_matches':sum(r['match'] for r in results),
        'index_build_ms':round(index_ms,3),
        'retrieval_p50_ms':round(statistics.median(latencies),3),
        'retrieval_p95_ms':round(latencies[int(.95*(len(latencies)-1))],3),
        'measured_queries':len(latencies),
        'limitations':'Local timing on this machine only. Questions were used during debugging: this is a regression set, not an unbiased held-out accuracy estimate. No Google API response, first-token latency, concurrency load or generated-answer accuracy was measured.',
        'results':results}
    (ROOT/'docs/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
    for row in results:
        if not row['match']:print('Mismatch:',row['question_id'],row['expected_intent'],row['actual_intent'])

if __name__=='__main__':main()
