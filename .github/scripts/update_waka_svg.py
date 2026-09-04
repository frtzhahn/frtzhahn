#!/usr/bin/env python3
"""
update_waka_svg.py
Dynamically builds a Pure Native SVG terminal dashboard (profile.svg) for GitHub Readme.
Eliminates <foreignObject> entirely to fix iOS/iPadOS WebKit rendering bugs (WebKit #23113).
Maintains Tokyo Night dark aesthetic and 25-second animation timeline.
"""

import json
import os
import sys
import re
import xml.etree.ElementTree as ET
import html

# ---------------------------------------------------------------------------
# 1. Mascot Vector Data Loader
# ---------------------------------------------------------------------------
def load_mocha_mascot():
    """Loads Mocha mascot SVG vector paths from .github/assets/mocha.svg."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, '..', 'assets', 'mocha.svg'),
        '.github/assets/mocha.svg',
        os.path.join(script_dir, 'assets', 'mocha.svg')
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    content = f.read()
                    inner = re.search(r'<svg[^>]*>(.*?)</svg>', content, re.DOTALL)
                    if inner:
                        return f'<svg width="120" height="120" viewBox="0 0 500 500">\n{inner.group(1)}\n        </svg>'
            except Exception as e:
                print(f"Warning: Failed reading {p}: {e}", file=sys.stderr)
    raise FileNotFoundError("Could not find .github/assets/mocha.svg mascot vector file.")

# ---------------------------------------------------------------------------
# 2. Dynamic Data Extractors & Normalizers
# ---------------------------------------------------------------------------
def load_wakatime_stats():
    """Loads WakaTime stats from stats.json or returns default fallback."""
    stats_file = 'stats.json'
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('data', {})
        except Exception as e:
            print(f"Warning: Failed to load {stats_file}: {e}", file=sys.stderr)

    # Fallback to current stats if available
    scratch_stats = '/home/mocha/.gemini/antigravity/brain/9902bcb0-2b7f-4bc0-a254-6c48f68c12a2/scratch/current_stats.json'
    if os.path.exists(scratch_stats):
        try:
            with open(scratch_stats, 'r', encoding='utf-8') as f:
                raw = json.load(f)
                return {
                    'languages': raw.get('languages', []),
                    'editors': [{'name': x} for x in raw.get('editors', [])],
                    'projects': [{'name': x} for x in raw.get('projects', [])],
                    'operating_systems': [{'name': x} for x in raw.get('os', [])],
                    'human_readable_total_including_other_language': raw.get('stat_time', '24 hrs 33 mins').replace(' total', ''),
                    'human_readable_daily_average_including_other_language': raw.get('stat_avg', '4 hrs 5 mins').replace(' / day', '')
                }
        except Exception:
            pass

    return {}

def load_skills():
    """Loads skills from .github/scripts/skills.json."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, 'skills.json'),
        '.github/scripts/skills.json',
        '/home/mocha/.gemini/antigravity/brain/9902bcb0-2b7f-4bc0-a254-6c48f68c12a2/scratch/skills_data.json'
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                elif isinstance(data, list):
                    return {
                        'operating_systems': [{'name': n, 'icon': ic} for ic, n in data[0:5]],
                        'editors': [{'name': n, 'icon': ic} for ic, n in data[5:11]],
                        'desktop_environments': [{'name': n, 'icon': ic} for ic, n in data[11:16]],
                        'languages_tools': [{'name': n, 'icon': ic} for ic, n in data[16:27]]
                    }
    return {'operating_systems': [], 'editors': [], 'desktop_environments': [], 'languages_tools': []}

# ---------------------------------------------------------------------------
# 3. Pure Native SVG Generator
# ---------------------------------------------------------------------------
def generate_native_profile_svg(stats, skills):
    """Generates pure native SVG markup with exact coordinate tracking."""
    mocha_mascot_svg = load_mocha_mascot()

    # Data extraction
    langs_raw = stats.get('languages', [])
    editors_raw = [e.get('name') if isinstance(e, dict) else str(e) for e in stats.get('editors', [])]
    projects_raw = [p.get('name') if isinstance(p, dict) else str(p) for p in stats.get('projects', [])]
    os_raw = [o.get('name') if isinstance(o, dict) else str(o) for o in stats.get('operating_systems', [])]

    time_str = stats.get('human_readable_total_including_other_language', '0 secs') + ' total'
    avg_str = stats.get('human_readable_daily_average_including_other_language', '0 secs') + ' / day'

    # ---------------- Layout Calculation Engine ----------------
    y_cursor = 30 # Base height below window title bar

    # Section 1: Fastfetch
    y_fastfetch_prompt = y_cursor + 24 # 54
    y_fastfetch_block = y_fastfetch_prompt + 20 # 74
    y_cursor = y_fastfetch_block + 130 # 204

    # Section 2: Bio
    y_bio_prompt = y_cursor + 24 # 228
    y_bio_block = y_bio_prompt + 24 # 252
    y_bio_1 = y_bio_block
    y_bio_2 = y_bio_block + 20
    y_bio_3 = y_bio_block + 40
    y_cursor = y_bio_3 + 28 # 320

    # Section 3: WakaTime
    y_waka_prompt = y_cursor
    y_waka_block = y_waka_prompt + 26
    y_waka_curr = y_waka_block

    # Languages list
    langs_svg_lines = []
    y_waka_curr += 20 # after "LANGUAGES" header
    for l in langs_raw:
        name = html.escape(l.get('name', 'Unknown'))
        pct = round(l.get('percent', 0), 1)
        color = l.get('color') or '#7aa2f7'
        bar_w = round(370 * (pct / 100.0), 1)
        langs_svg_lines.append(f"""
      <g class="waka-bar-row">
        <text x="20" y="{y_waka_curr}" class="waka-lang-name">{name}</text>
        <rect x="135" y="{y_waka_curr - 9}" width="370" height="8" rx="4" class="bar-bg" />
        <rect x="135" y="{y_waka_curr - 9}" width="{bar_w}" height="8" rx="4" fill="{color}" class="bar-fill" />
        <text x="580" y="{y_waka_curr}" text-anchor="end" class="waka-lang-val">{pct}%</text>
      </g>""")
        y_waka_curr += 22

    y_waka_curr += 15
    y_waka_lists_top = y_waka_curr

    # Left column: Active Editors, Operating Systems, Performance (x=20)
    y_left = y_waka_lists_top
    editors_svg = []
    y_left += 20
    for ed in editors_raw:
        editors_svg.append(f'<text x="20" y="{y_left}" class="stat-item"><tspan fill="#414868">●</tspan> {html.escape(ed)}</text>')
        y_left += 18

    y_left += 15
    y_os_header = y_left
    y_left += 20
    os_svg = []
    for o in os_raw:
        os_svg.append(f'<text x="20" y="{y_left}" class="stat-item"><tspan fill="#414868">●</tspan> {html.escape(o)}</text>')
        y_left += 18

    y_left += 15
    y_perf_header = y_left
    y_left += 20
    perf_svg = [
        f'<text x="20" y="{y_left}" class="stat-item"><tspan fill="#7aa2f7" font-weight="bold">TIME:</tspan> <tspan id="stat-time">{html.escape(time_str)}</tspan></text>',
        f'<text x="20" y="{y_left + 18}" class="stat-item"><tspan fill="#9ece6a" font-weight="bold">DAILY AVG:</tspan> <tspan id="stat-avg">{html.escape(avg_str)}</tspan></text>'
    ]
    y_left += 36

    # Right column: Current Projects (x=310)
    y_right = y_waka_lists_top
    projects_svg = []
    y_right += 20
    for prj in projects_raw:
        projects_svg.append(f'<text x="310" y="{y_right}" class="stat-item stat-project"><tspan fill="#414868">●</tspan> {html.escape(prj)}</text>')
        y_right += 18

    y_cursor = max(y_left, y_right) + 28

    # Section 4: Skills
    y_skills_prompt = y_cursor
    y_skills_block = y_skills_prompt + 26
    y_skills_top = y_skills_block

    # Left column skills (x=20)
    y_sk_left = y_skills_top + 20
    sk_os_svg = []
    for item in skills.get('operating_systems', []):
        sk_os_svg.append(f'''<g class="skill-entry">
      <image href="{item['icon']}" x="20" y="{y_sk_left - 13}" width="16" height="16" />
      <text x="44" y="{y_sk_left}" class="skill-name">{html.escape(item['name'])}</text>
    </g>''')
        y_sk_left += 22

    y_sk_left += 15
    y_sk_ed_header = y_sk_left
    y_sk_left += 20
    sk_ed_svg = []
    for item in skills.get('editors', []):
        sk_ed_svg.append(f'''<g class="skill-entry">
      <image href="{item['icon']}" x="20" y="{y_sk_left - 13}" width="16" height="16" />
      <text x="44" y="{y_sk_left}" class="skill-name">{html.escape(item['name'])}</text>
    </g>''')
        y_sk_left += 22

    # Right column skills (x=310)
    y_sk_right = y_skills_top + 20
    sk_de_svg = []
    for item in skills.get('desktop_environments', []):
        sk_de_svg.append(f'''<g class="skill-entry">
      <image href="{item['icon']}" x="310" y="{y_sk_right - 13}" width="16" height="16" />
      <text x="334" y="{y_sk_right}" class="skill-name">{html.escape(item['name'])}</text>
    </g>''')
        y_sk_right += 22

    y_sk_right += 15
    y_sk_lt_header = y_sk_right
    y_sk_right += 20
    sk_lt_svg = []
    for item in skills.get('languages_tools', []):
        sk_lt_svg.append(f'''<g class="skill-entry">
      <image href="{item['icon']}" x="310" y="{y_sk_right - 13}" width="16" height="16" />
      <text x="334" y="{y_sk_right}" class="skill-name">{html.escape(item['name'])}</text>
    </g>''')
        y_sk_right += 22

    y_cursor = max(y_sk_left, y_sk_right) + 28

    # Section 5: Bottom cursor and footer
    y_final_prompt = y_cursor
    total_height = y_final_prompt + 55
    y_footer = total_height - 12

    # ---------------- SVG Assembly ----------------
    svg_out = f"""<svg viewBox="0 0 600 {total_height}" width="600" height="{total_height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Typewriter Clip Paths (Using scaleX for 100% WebKit hardware compatibility) -->
    <clipPath id="clip-fastfetch">
      <rect class="clip-stencil clip-fastfetch-anim" x="145" y="{y_fastfetch_prompt - 16}" width="120" height="24" />
    </clipPath>
    <clipPath id="clip-cat">
      <rect class="clip-stencil clip-cat-anim" x="145" y="{y_bio_prompt - 16}" width="180" height="24" />
    </clipPath>
    <clipPath id="clip-htop">
      <rect class="clip-stencil clip-htop-anim" x="145" y="{y_waka_prompt - 16}" width="140" height="24" />
    </clipPath>
    <clipPath id="clip-skills">
      <rect class="clip-stencil clip-skills-anim" x="145" y="{y_skills_prompt - 16}" width="180" height="24" />
    </clipPath>

    <!-- Bio Sequential Line Clip Paths -->
    <clipPath id="clip-bio-1">
      <rect class="clip-stencil clip-bio1-anim" x="20" y="{y_bio_1 - 16}" width="560" height="24" />
    </clipPath>
    <clipPath id="clip-bio-2">
      <rect class="clip-stencil clip-bio2-anim" x="20" y="{y_bio_2 - 16}" width="560" height="24" />
    </clipPath>
    <clipPath id="clip-bio-3">
      <rect class="clip-stencil clip-bio3-anim" x="20" y="{y_bio_3 - 16}" width="560" height="24" />
    </clipPath>
  </defs>

  <style>
    /* Typography and Base Styles */
    text {{
      font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'DejaVu Sans Mono', monospace;
      dominant-baseline: alphabetic;
    }}

    .prompt-host {{ fill: #bb9af7; font-size: 14px; }}
    .prompt-colon {{ fill: #a9b1d6; font-size: 14px; }}
    .prompt-dir   {{ fill: #7aa2f7; font-weight: bold; font-size: 14px; }}
    .prompt-char  {{ fill: #a9b1d6; font-size: 14px; }}
    .cmd-text     {{ fill: #7aa2f7; font-size: 14px; }}

    .cmd-cursor {{
      fill: #7aa2f7;
      font-size: 14px;
      animation: cursor-blink 0.8s infinite;
    }}
    @keyframes cursor-blink {{
      0%, 49% {{ opacity: 1; }}
      50%, 100% {{ opacity: 0; }}
    }}

    /* Stencil Transforms for WebKit compatibility */
    .clip-stencil {{
      transform-box: fill-box;
      transform-origin: left;
    }}

    .clip-fastfetch-anim {{ animation: type-fastfetch 25s infinite; }}
    .clip-cat-anim       {{ animation: type-cat 25s infinite; }}
    .clip-htop-anim      {{ animation: type-htop 25s infinite; }}
    .clip-skills-anim    {{ animation: type-skills 25s infinite; }}

    @keyframes type-fastfetch {{
      0%, 4.0% {{ transform: scaleX(0); }}
      12.0%, 92.0% {{ transform: scaleX(1); }}
      98.0%, 100% {{ transform: scaleX(0); }}
    }}
    @keyframes type-cat {{
      0%, 4.0% {{ transform: scaleX(0); }}
      12.0%, 92.0% {{ transform: scaleX(1); }}
      98.0%, 100% {{ transform: scaleX(0); }}
    }}
    @keyframes type-htop {{
      0%, 4.0% {{ transform: scaleX(0); }}
      12.0%, 92.0% {{ transform: scaleX(1); }}
      98.0%, 100% {{ transform: scaleX(0); }}
    }}
    @keyframes type-skills {{
      0%, 4.0% {{ transform: scaleX(0); }}
      12.0%, 92.0% {{ transform: scaleX(1); }}
      98.0%, 100% {{ transform: scaleX(0); }}
    }}

    /* Bio Sequential Keyframes */
    .clip-bio1-anim {{ animation: type-bio-1 25s infinite; }}
    .clip-bio2-anim {{ animation: type-bio-2 25s infinite; }}
    .clip-bio3-anim {{ animation: type-bio-3 25s infinite; }}

    @keyframes type-bio-1 {{
      0%, 8.0% {{ transform: scaleX(0); }}
      18.0%, 72.0% {{ transform: scaleX(1); }}
      88.0%, 100% {{ transform: scaleX(0); }}
    }}
    @keyframes type-bio-2 {{
      0%, 18.0% {{ transform: scaleX(0); }}
      28.0%, 72.0% {{ transform: scaleX(1); }}
      88.0%, 100% {{ transform: scaleX(0); }}
    }}
    @keyframes type-bio-3 {{
      0%, 28.0% {{ transform: scaleX(0); }}
      38.0%, 72.0% {{ transform: scaleX(1); }}
      88.0%, 100% {{ transform: scaleX(0); }}
    }}

    /* Output Fades (Fastfetch, Bio, Waka, Skills) */
    .output-fade {{
      animation: output-fade-anim 25s infinite;
    }}
    @keyframes output-fade-anim {{
      0%, 12.0% {{ opacity: 0; }}
      32.0%, 72.0% {{ opacity: 1; }}
      92.0%, 100% {{ opacity: 0; }}
    }}

    /* Progress Bar Fills */
    .bar-bg {{ fill: #24283b; }}
    .bar-fill {{
      transform-box: fill-box;
      transform-origin: left;
      animation: fill-bar-anim 25s infinite;
    }}
    @keyframes fill-bar-anim {{
      0%, 12.0% {{ transform: scaleX(0); }}
      32.0%, 72.0% {{ transform: scaleX(1); }}
      92.0%, 100% {{ transform: scaleX(0); }}
    }}

    /* Fastfetch Styles */
    .ff-spec-label {{ fill: #7aa2f7; font-size: 11px; }}
    .ff-spec-val   {{ fill: #a9b1d6; font-size: 11px; }}
    .ff-course-hdr {{ fill: #7aa2f7; font-weight: bold; font-size: 11px; }}
    .ff-course-val {{ fill: #a9b1d6; font-size: 11px; }}

    /* Bio Styles */
    .bio-line   {{ fill: #9ece6a; font-size: 12px; }}
    .bio-accent {{ fill: #bb9af7; font-weight: bold; font-size: 12px; }}

    /* WakaTime Styles */
    .section-title {{ fill: #565f89; font-size: 14px; font-weight: bold; text-transform: uppercase; }}
    .waka-lang-name {{ fill: #7aa2f7; font-size: 11px; }}
    .waka-lang-val  {{ fill: #a9b1d6; font-size: 11px; }}
    .stat-item      {{ fill: #a9b1d6; font-size: 12px; }}
    .stat-project   {{ fill: #7dcfff; }}

    /* Skills Styles */
    .skills-hdr  {{ fill: #565f89; font-size: 13px; font-weight: bold; text-transform: uppercase; }}
    .skill-name  {{ fill: #a9b1d6; font-size: 12px; }}

    /* Footer */
    .footer-text {{ fill: #414868; font-size: 10px; }}
    .footer-en-cours {{ fill: #bb9af7; font-size: 10px; font-weight: bold; }}

    /* Reduced Motion Accessibility */
    @media (prefers-reduced-motion: reduce) {{
      *, .clip-stencil, .output-fade, .bar-fill {{
        animation: none !important;
        opacity: 1 !important;
        transform: none !important;
      }}
    }}
  </style>

  <!-- Window Frame Background -->
  <rect x="0.5" y="0.5" width="599" height="{total_height - 1}" rx="6" fill="#1a1b26" stroke="#414868" />

  <!-- Window Header -->
  <path d="M0.5 6.5A6 6 0 0 1 6.5 0.5H593.5A6 6 0 0 1 599.5 6.5V30.5H0.5Z" fill="#1f2335" />
  <line x1="0" y1="30.5" x2="600" y2="30.5" stroke="#414868" />
  <circle cx="21" cy="15.5" r="5" fill="#f7768e" />
  <circle cx="37" cy="15.5" r="5" fill="#e0af68" />
  <circle cx="53" cy="15.5" r="5" fill="#9ece6a" />
  <text x="300" y="19" text-anchor="middle" fill="#565f89" font-size="11">aldrin@frtzhahn: ~</text>

  <!-- ==================== 1. FASTFETCH ==================== -->
  <g id="fastfetch-section">
    <text x="20" y="{y_fastfetch_prompt}">
      <tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan><tspan class="cmd-text" clip-path="url(#clip-fastfetch)">fastfetch</tspan><tspan class="cmd-cursor"> _</tspan>
    </text>

    <g class="output-fade">
      <!-- Mocha Avatar -->
      <g id="fastfetch-avatar" transform="translate(20, {y_fastfetch_block})">
        {mocha_mascot_svg}
      </g>

      <!-- System Specs -->
      <g id="fastfetch-specs">
        <!-- will_to_code -->
        <text x="160" y="{y_fastfetch_block + 18}" class="ff-spec-label">will_to_code</text>
        <rect x="255" y="{y_fastfetch_block + 10}" width="250" height="8" rx="4" class="bar-bg" />
        <rect x="255" y="{y_fastfetch_block + 10}" width="125" height="8" rx="4" fill="#bb9af7" class="bar-fill" />
        <text x="545" y="{y_fastfetch_block + 18}" class="ff-spec-val">50%</text>

        <!-- irl_age -->
        <text x="160" y="{y_fastfetch_block + 40}" class="ff-spec-label" fill="#bb9af7">irl_age</text>
        <rect x="255" y="{y_fastfetch_block + 32}" width="250" height="8" rx="4" class="bar-bg" />
        <rect x="255" y="{y_fastfetch_block + 32}" width="45" height="8" rx="4" fill="#bb9af7" class="bar-fill" />
        <text x="545" y="{y_fastfetch_block + 40}" class="ff-spec-val">18%</text>

        <!-- college_level -->
        <text x="160" y="{y_fastfetch_block + 62}" class="ff-spec-label" fill="#bb9af7">college_level</text>
        <rect x="255" y="{y_fastfetch_block + 54}" width="250" height="8" rx="4" class="bar-bg" />
        <rect x="255" y="{y_fastfetch_block + 54}" width="62.5" height="8" rx="4" fill="#f79acf" class="bar-fill" />
        <text x="545" y="{y_fastfetch_block + 62}" class="ff-spec-val">25%</text>

        <line x1="160" y1="{y_fastfetch_block + 78}" x2="570" y2="{y_fastfetch_block + 78}" stroke="#414868" stroke-dasharray="4,4" />

        <!-- Course & Traits -->
        <text x="160" y="{y_fastfetch_block + 96}">
          <tspan class="ff-course-hdr">COURSE</tspan><tspan class="ff-course-val">: Bachelor of Science in Computer Science</tspan>
        </text>
        <text x="160" y="{y_fastfetch_block + 116}">
          <tspan class="ff-course-hdr">TRAITS</tspan><tspan class="ff-course-val">: Procrastinator, Crammer, Night Owl</tspan>
        </text>
      </g>
    </g>
  </g>

  <!-- ==================== 2. BIO ==================== -->
  <g id="bio-section">
    <text x="20" y="{y_bio_prompt}">
      <tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan><tspan class="cmd-text" clip-path="url(#clip-cat)">cat about_me.txt</tspan><tspan class="cmd-cursor"> _</tspan>
    </text>

    <g class="output-fade">
      <text x="20" y="{y_bio_1}" clip-path="url(#clip-bio-1)">
        <tspan class="bio-line">&gt; Hello, I'm </tspan><tspan class="bio-accent">Aldrin James A. Alciso</tspan>
      </text>
      <text x="20" y="{y_bio_2}" clip-path="url(#clip-bio-2)">
        <tspan class="bio-line">&gt; Student at </tspan><tspan class="bio-accent">University of Caloocan City</tspan>
      </text>
      <text x="20" y="{y_bio_3}" clip-path="url(#clip-bio-3)">
        <tspan class="bio-line">&gt; Exploring new things everyday :3</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== 3. WAKATIME ==================== -->
  <g id="wakatime-section">
    <text x="20" y="{y_waka_prompt}">
      <tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan><tspan class="cmd-text" clip-path="url(#clip-htop)">htop --stats</tspan><tspan class="cmd-cursor"> _</tspan>
    </text>

    <g class="output-fade">
      <!-- Languages Section -->
      <text x="20" y="{y_waka_block}" class="section-title">LANGUAGES</text>
      <line x1="20" y1="{y_waka_block + 6}" x2="580" y2="{y_waka_block + 6}" stroke="#24283b" />
      <!-- LANG_START -->
{''.join(langs_svg_lines)}
      <!-- LANG_END -->

      <!-- Left Column: Active Editors, OS, Performance -->
      <!-- Editors -->
      <text x="20" y="{y_waka_lists_top}" class="section-title">ACTIVE EDITORS</text>
      <line x1="20" y1="{y_waka_lists_top + 6}" x2="280" y2="{y_waka_lists_top + 6}" stroke="#24283b" />
      <!-- EDITORS_START -->
      {''.join(editors_svg)}
      <!-- EDITORS_END -->

      <!-- OS -->
      <text x="20" y="{y_os_header}" class="section-title">OPERATING SYSTEMS</text>
      <line x1="20" y1="{y_os_header + 6}" x2="280" y2="{y_os_header + 6}" stroke="#24283b" />
      <!-- OS_START -->
      {''.join(os_svg)}
      <!-- OS_END -->

      <!-- Performance -->
      <text x="20" y="{y_perf_header}" class="section-title">aldrin@frtzhahn performance</text>
      <line x1="20" y1="{y_perf_header + 6}" x2="280" y2="{y_perf_header + 6}" stroke="#24283b" />
      {''.join(perf_svg)}

      <!-- Right Column: Current Projects -->
      <text x="310" y="{y_waka_lists_top}" class="section-title">CURRENT PROJECTS</text>
      <line x1="310" y1="{y_waka_lists_top + 6}" x2="580" y2="{y_waka_lists_top + 6}" stroke="#24283b" />
      <!-- PROJECTS_START -->
      {''.join(projects_svg)}
      <!-- PROJECTS_END -->
    </g>
  </g>

  <!-- ==================== 4. SKILLS ==================== -->
  <g id="skills-section">
    <text x="20" y="{y_skills_prompt}">
      <tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan><tspan class="cmd-text" clip-path="url(#clip-skills)">cat ~/skills.txt</tspan><tspan class="cmd-cursor"> _</tspan>
    </text>

    <g class="output-fade">
      <!-- Left Column Skills -->
      <text x="20" y="{y_skills_top}" class="skills-hdr">OPERATING SYSTEMS</text>
      <line x1="20" y1="{y_skills_top + 6}" x2="280" y2="{y_skills_top + 6}" stroke="#24283b" />
      {''.join(sk_os_svg)}

      <text x="20" y="{y_sk_ed_header}" class="skills-hdr">EDITORS &amp; IDES</text>
      <line x1="20" y1="{y_sk_ed_header + 6}" x2="280" y2="{y_sk_ed_header + 6}" stroke="#24283b" />
      {''.join(sk_ed_svg)}

      <!-- Right Column Skills -->
      <text x="310" y="{y_skills_top}" class="skills-hdr">DESKTOP ENVIRONMENTS</text>
      <line x1="310" y1="{y_skills_top + 6}" x2="580" y2="{y_skills_top + 6}" stroke="#24283b" />
      {''.join(sk_de_svg)}

      <text x="310" y="{y_sk_lt_header}" class="skills-hdr">LANGUAGES/TOOLS</text>
      <line x1="310" y1="{y_sk_lt_header + 6}" x2="580" y2="{y_sk_lt_header + 6}" stroke="#24283b" />
      {''.join(sk_lt_svg)}
    </g>
  </g>

  <!-- ==================== 5. FOOTER ==================== -->
  <g id="footer-section">
    <text x="20" y="{y_final_prompt}">
      <tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan><tspan class="cmd-cursor">_</tspan>
    </text>

    <line x1="0" y1="{total_height - 28}" x2="600" y2="{total_height - 28}" stroke="#24283b" />
    <text x="20" y="{y_footer}" class="footer-text">LOGS: monitoring pid 1476</text>
    <text x="580" y="{y_footer}" text-anchor="end" class="footer-en-cours">"STATUS: EN_COURS"</text>
  </g>
</svg>
"""
    return svg_out, total_height

# ---------------------------------------------------------------------------
# 4. Entrypoint & XML Validation
# ---------------------------------------------------------------------------
def main():
    print("Fetching and building pure native profile SVG...")
    stats = load_wakatime_stats()
    skills = load_skills()

    svg_content, total_height = generate_native_profile_svg(stats, skills)

    # Validate XML syntax before writing
    try:
        ET.fromstring(svg_content)
        print("XML Syntax Validation: PASSED (Well-formed SVG)")
    except ET.ParseError as e:
        print(f"Error: Generated SVG is not well-formed XML: {e}", file=sys.stderr)
        sys.exit(1)

    with open('profile.svg', 'w', encoding='utf-8') as f:
        f.write(svg_content)

    num_langs = len(stats.get('languages', []))
    num_editors = len(stats.get('editors', []))
    num_projects = len(stats.get('projects', []))
    print(f"Successfully generated profile.svg:")
    print(f"  - Height: {total_height}px")
    print(f"  - Languages: {num_langs}")
    print(f"  - Editors: {num_editors}")
    print(f"  - Projects: {num_projects}")

if __name__ == '__main__':
    main()
