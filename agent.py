import csv, json, pathlib, datetime
ROOT=pathlib.Path(__file__).parent
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
leads=DATA/'companies.csv'
if not leads.exists():
 with leads.open('w',newline='',encoding='utf-8') as f: csv.writer(f).writerow(['company','country','website','public_contact','source_url','permission_status','status'])
rows=list(csv.DictReader(leads.open(encoding='utf-8')))
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
report={'run_utc':now,'companies_in_review':len(rows),'approved_to_contact':sum(r.get('permission_status')=='approved' for r in rows),'note':'No external search API configured. No emails sent, no property listings published. Add verified company records and obtain permissions before outreach.'}
(DATA/'latest_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(DATA/'report.md').write_text('# AS for the Best Life — Operations report\n\nRun: '+now+'\n\nCompanies recorded: '+str(len(rows))+'\n\nNo live search integration configured. No messages sent or properties published.\n',encoding='utf-8')
print(json.dumps(report))
