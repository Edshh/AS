import csv
import datetime as dt
import json
import pathlib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)
CSV = DATA / 'companies.csv'
FIELDS = ['company', 'country', 'website', 'public_contact', 'source_url', 'permission_status', 'status']
if not CSV.exists():
    with CSV.open('w', newline='', encoding='utf-8') as f:
        csv.DictWriter(f, fieldnames=FIELDS).writeheader()

with CSV.open(newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    existing = list(reader)
    fields = list(dict.fromkeys((reader.fieldnames or []) + FIELDS))

# Google News RSS offers publicly indexed leads; these are NOT verified companies.
queries = {
    'UAE': 'real estate developer Dubai company',
    'Saudi Arabia': 'real estate developer Saudi Arabia company',
    'USA': 'real estate brokerage company United States',
}
items = []
errors = []
for country, query in queries.items():
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({
        'q': query, 'hl': 'en', 'gl': 'US', 'ceid': 'US:en'
    })
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'AS-Research-Agent/1.0 (public RSS)'})
        with urllib.request.urlopen(request, timeout=18) as response:
            root = ET.fromstring(response.read(750_000))
        for entry in root.findall('./channel/item')[:10]:
            title = (entry.findtext('title') or '').strip()
            link = (entry.findtext('link') or '').strip()
            if title and link:
                items.append({'country': country, 'headline': title, 'source_url': link,
                              'review_status': 'needs_manual_verification'})
    except Exception as exc:
        errors.append({'country': country, 'error': str(exc)[:180]})

# News headlines are research leads, never automatically added as verified companies.
seen = set()
unique = []
for item in items:
    if item['source_url'] not in seen:
        seen.add(item['source_url'])
        unique.append(item)

now = dt.datetime.now(dt.timezone.utc).isoformat()
report = {
    'run_utc': now,
    'companies_in_review': len(existing),
    'approved_to_contact': sum(r.get('permission_status') == 'approved' for r in existing),
    'research_leads_found': len(unique),
    'research_errors': errors,
    'note': 'RSS headlines are unverified research leads, not confirmed companies. No messages sent or listings published.'
}
(DATA / 'research_leads.json').write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding='utf-8')
(DATA / 'latest_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
lines = ['# AS for the Best Life — Research Report', '', 'Run: ' + now,
         'Unverified news leads: ' + str(len(unique)),
         'Companies recorded: ' + str(len(existing)), '',
         'All leads require verification. No outreach or publishing performed.', '']
for item in unique:
    lines.append('- [' + item['country'] + '] ' + item['headline'].replace('\n', ' ') + ' — ' + item['source_url'])
if errors:
    lines.extend(['', '## Fetch errors', json.dumps(errors, ensure_ascii=False, indent=2)])
(DATA / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
