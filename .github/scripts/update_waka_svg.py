import json, re, sys

with open('stats.json') as f:
    stats = json.load(f).get('data', {})

with open('wakatime.svg', 'r') as f:
    svg = f.read()

# ── Debug: print what the API actually returned ───────────────────────────────
time_str = stats.get('human_readable_total_including_other_language', '0 secs')
avg_str  = stats.get('human_readable_daily_average_including_other_language', '0 secs')
langs_raw = stats.get('languages', [])
print(f"API → total={time_str!r}, avg={avg_str!r}, {len(langs_raw)} languages:")
for l in langs_raw:
    print(f"  {l['name']}: {round(l.get('percent',0),1)}%")

def generate_list(items, template):
    return '\n'.join([template.format(item=i) for i in items]) \
        if items else '                <div class="stat-item">● No data</div>'

# Languages
langs = []
for l in langs_raw:
    color = l.get('color') or '#7aa2f7'
    pct   = round(l.get('percent', 0), 1)
    langs.append(
        f'              <div class="bar-row">'
        f'<span class="bar-name">{l["name"]}</span>'
        f'<div class="bar-bg"><div class="bar-fill" style="width: {pct}%; background: {color};"></div></div>'
        f'<span class="bar-val">{pct}%</span></div>'
    )

svg = re.sub(
    r'(<!-- LANG_START -->).*?(<!-- LANG_END -->)',
    r'\1\n' + '\n'.join(langs) + r'\n              \2',
    svg, flags=re.DOTALL
)

# Editors
editors = generate_list(stats.get('editors', []),
    '                <div class="stat-item">● {item[name]}</div>')
svg = re.sub(
    r'(<!-- EDITORS_START -->).*?(<!-- EDITORS_END -->)',
    r'\1\n' + editors + r'\n                \2',
    svg, flags=re.DOTALL
)

# Projects
projects = generate_list(stats.get('projects', []),
    '                <div class="stat-item">● {item[name]}</div>')
svg = re.sub(
    r'(<!-- PROJECTS_START -->).*?(<!-- PROJECTS_END -->)',
    r'\1\n' + projects + r'\n                \2',
    svg, flags=re.DOTALL
)

# OS
oss = generate_list(stats.get('operating_systems', []),
    '                <div class="stat-item">● {item[name]}</div>')
svg = re.sub(
    r'(<!-- OS_START -->).*?(<!-- OS_END -->)',
    r'\1\n' + oss + r'\n                \2',
    svg, flags=re.DOTALL
)

# Time & Performance
svg = re.sub(r'<span id="stat-time">[^<]*</span>', f'<span id="stat-time">{time_str} total</span>', svg)
svg = re.sub(r'<span id="stat-avg">[^<]*</span>',  f'<span id="stat-avg">{avg_str} / day</span>',   svg)

# Dynamic height
total_langs = len(langs_raw)
total_items = (len(stats.get('editors', []))
             + len(stats.get('projects', []))
             + len(stats.get('operating_systems', [])))
new_height  = max(250 + (total_langs * 25) + (total_items * 18), 600)

svg = re.sub(r'viewBox="0 0 600 \d+"',              f'viewBox="0 0 600 {new_height + 20}"', svg)
svg = re.sub(r'(\.container\s*\{[^}]*?)height:\s*\d+px;',
             fr'\1height: {new_height}px;', svg, flags=re.DOTALL)

with open('wakatime.svg', 'w') as f:
    f.write(svg)

print(f"Written: {total_langs} langs, height={new_height}px, time={time_str!r}, avg={avg_str!r}")
