#!/usr/bin/env python3
"""
update_waka_svg.py
Dynamically builds a Pure Native SVG terminal dashboard (profile.svg) for GitHub Readme.
Eliminates <foreignObject> entirely to fix iOS/iPadOS WebKit rendering bugs (WebKit #23113).
Maintains Gruvbox Dark aesthetic and 10.0-second One-Shot entrance animation timeline.
Features smooth continuous typography unmasking and synchronized Gruvbox Bright Aqua vertical cursor bars.
"""

import json
import os
import sys
import re
import xml.etree.ElementTree as ET
import html


# ===========================================================================
# THEME CONFIGURATION
# To switch themes, uncomment the desired THEME dictionary and comment out the other.
# ===========================================================================

# --- Tokyo Night (Original) ---
# THEME = {
#     'name': 'Tokyo Night',
#     'bg': '#1a1b26',
#     'header_bg': '#1f2335',
#     'tab_bg': '#16161e',
#     'border': '#414868',
#     'divider': '#24283b',
#     'bar_bg': '#24283b',
#     'fg': '#a9b1d6',
#     'fg_muted': '#565f89',
#     'fg_subtle': '#414868',
#     'prompt_host': '#bb9af7',
#     'prompt_colon': '#a9b1d6',
#     'prompt_dir': '#7aa2f7',
#     'cmd': '#7aa2f7',
#     'cursor': '#7aa2f7',
#     'tab_accent': '#7aa2f7',
#     'content_cursor': '#7aa2f7',
#     'fastfetch_spec_label': '#7aa2f7',
#     'fastfetch_course_hdr': '#7aa2f7',
#     'pr_bar': '#bb9af7',
#     'issue_bar': '#7aa2f7',
#     'streak_bar': '#73daca',
#     'bio_line': '#9ece6a',
#     'bio_accent': '#bb9af7',
#     'section_title': '#565f89',
#     'waka_lang_name': '#7aa2f7',
#     'stat_bullet': '#414868',
#     'stat_project': '#7dcfff',
#     'perf_time_label': '#7aa2f7',
#     'perf_avg_label': '#9ece6a',
#     'skills_hdr': '#565f89',
#     'footer_text': '#414868',
#     'footer_badge': '#bb9af7',
#     'dot_red': '#f7768e',
#     'dot_yellow': '#e0af68',
#     'dot_green': '#9ece6a',
# }

# --- Gruvbox Dark (Active) ---
THEME = {
    'name': 'Gruvbox Dark',
    'bg': '#282828',             # dark0
    'header_bg': '#1d2021',      # dark0_hard
    'tab_bg': '#282828',         # dark0 active tab background
    'border': '#504945',         # dark2
    'divider': '#3c3836',        # dark1
    'bar_bg': '#3c3836',         # dark1
    'fg': '#ebdbb2',             # light1
    'fg_muted': '#a89984',       # light4
    'fg_subtle': '#928374',      # gray
    'prompt_host': '#d3869b',    # bright purple
    'prompt_colon': '#a89984',   # light4
    'prompt_dir': '#83a598',     # bright blue
    'cmd': '#8ec07c',            # bright aqua
    'cursor': '#fe8019',         # bright orange
    'tab_accent': '#fe8019',     # bright orange
    'content_cursor': '#8ec07c', # bright aqua for content cursor bar
    'fastfetch_spec_label': '#83a598',  # bright blue
    'fastfetch_course_hdr': '#fabd2f',  # bright yellow
    'pr_bar': '#d3869b',         # bright purple
    'issue_bar': '#83a598',      # bright blue
    'streak_bar': '#8ec07c',     # bright aqua
    'bio_line': '#b8bb26',       # bright green
    'bio_accent': '#fabd2f',     # bright yellow
    'section_title': '#fe8019',  # bright orange
    'waka_lang_name': '#83a598', # bright blue
    'stat_bullet': '#928374',    # gray
    'stat_project': '#8ec07c',   # bright aqua
    'perf_time_label': '#83a598',# bright blue
    'perf_avg_label': '#b8bb26', # bright green
    'skills_hdr': '#fe8019',     # bright orange
    'footer_text': '#928374',    # gray
    'footer_badge': '#d3869b',   # bright purple
    'dot_red': '#fb4934',        # bright red
    'dot_yellow': '#fabd2f',     # bright yellow
    'dot_green': '#b8bb26',      # bright green
}

# ---------------------------------------------------------------------------
# 1. Mascot Vector Data Loader
# ---------------------------------------------------------------------------
def load_mocha_mascot(x=20, y=74):
    """Loads Mocha mascot SVG vector paths from .github/assets/mocha.svg with explicit viewport coordinates."""
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
                        return f'<svg x="{x}" y="{y}" width="120" height="120" viewBox="0 0 500 500">\n{inner.group(1)}\n        </svg>'
            except Exception as e:
                print(f"Warning: Failed reading {p}: {e}", file=sys.stderr)
    raise FileNotFoundError("Could not find .github/assets/mocha.svg mascot vector file.")

def fetch_github_stats(username="frtzhahn"):
    """
    Fetches PR, issue, and commit streak metrics from GitHub GraphQL API.
    Falls back gracefully to cached/sensible defaults if offline or unauthenticated.
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    defaults = {
        'pr_pct': 82.0,
        'pr_str': '82% (Merged)',
        'issue_pct': 65.0,
        'issue_str': '65% (Closed)',
        'streak_pct': 88.0,
        'streak_str': '88% (Goal: 365)'
    }

    cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'github_stats.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                defaults.update(cached)
        except Exception:
            pass

    if not token:
        try:
            import subprocess
            proc = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=2)
            if proc.returncode == 0 and proc.stdout.strip():
                token = proc.stdout.strip()
        except Exception:
            pass

    if not token:
        return defaults

    query = """
    query($login: String!) {
      user(login: $login) {
        pullRequests(first: 1) {
          totalCount
        }
        mergedPRs: pullRequests(states: [MERGED], first: 1) {
          totalCount
        }
        issues(first: 1) {
          totalCount
        }
        closedIssues: issues(states: [CLOSED], first: 1) {
          totalCount
        }
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    import urllib.request
    req_data = json.dumps({'query': query, 'variables': {'login': username}}).encode('utf-8')
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=req_data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'frtzhahn-profile-widget'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            user = res.get('data', {}).get('user', {})
            if not user:
                return defaults

            # 1. Pull Requests
            total_prs = user.get('pullRequests', {}).get('totalCount', 0)
            merged_prs = user.get('mergedPRs', {}).get('totalCount', 0)
            if total_prs > 0:
                pr_pct = round((merged_prs / total_prs) * 100, 1)
                pr_str = f"{int(pr_pct) if pr_pct.is_integer() else pr_pct}% (Merged)"
            else:
                pr_pct = defaults['pr_pct']
                pr_str = defaults['pr_str']

            # 2. Issues Solved
            total_issues = user.get('issues', {}).get('totalCount', 0)
            closed_issues = user.get('closedIssues', {}).get('totalCount', 0)
            if total_issues > 0:
                issue_pct = round((closed_issues / total_issues) * 100, 1)
                issue_str = f"{int(issue_pct) if issue_pct.is_integer() else issue_pct}% (Closed)"
            else:
                issue_pct = defaults['issue_pct']
                issue_str = defaults['issue_str']

            # 3. Commit Streak
            weeks = user.get('contributionsCollection', {}).get('contributionCalendar', {}).get('weeks', [])
            days = []
            for w in weeks:
                for d in w.get('contributionDays', []):
                    days.append((d.get('date'), d.get('contributionCount', 0)))

            days.sort(key=lambda x: x[0])
            streak = 0
            if days:
                rev_days = list(reversed(days))
                if rev_days and rev_days[0][1] == 0:
                    rev_days = rev_days[1:]
                for _, count in rev_days:
                    if count > 0:
                        streak += 1
                    else:
                        break

            if streak > 0:
                streak_pct = min(round((streak / 365.0) * 100, 1), 100.0)
                streak_str = f"{int(streak_pct) if streak_pct.is_integer() else streak_pct}% (Goal: 365)"
            else:
                streak_pct = defaults['streak_pct']
                streak_str = defaults['streak_str']

            stats_result = {
                'pr_pct': pr_pct,
                'pr_str': pr_str,
                'issue_pct': issue_pct,
                'issue_str': issue_str,
                'streak_pct': streak_pct,
                'streak_str': streak_str,
                'streak_days': streak
            }

            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(stats_result, f, indent=2)
            except Exception:
                pass

            return stats_result
    except Exception as e:
        print(f"Warning: GitHub GraphQL fetch failed ({e}); using cached/fallback metrics.", file=sys.stderr)
        return defaults


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

def generate_native_profile_svg(stats, skills, gh_stats=None):
    """Generates pure native SVG markup with exact coordinate tracking."""
    if gh_stats is None:
        gh_stats = fetch_github_stats()

    # GitHub fastfetch specs
    pr_pct = gh_stats.get('pr_pct', 82.0)
    pr_str = gh_stats.get('pr_str', '82% (Merged)')
    pr_bar_w = round(190 * (pr_pct / 100.0), 1)

    issue_pct = gh_stats.get('issue_pct', 65.0)
    issue_str = gh_stats.get('issue_str', '65% (Closed)')
    issue_bar_w = round(190 * (issue_pct / 100.0), 1)

    streak_pct = gh_stats.get('streak_pct', 88.0)
    streak_str = gh_stats.get('streak_str', '88% (Goal: 365)')
    streak_bar_w = round(190 * (streak_pct / 100.0), 1)

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
    mocha_mascot_svg = load_mocha_mascot(x=20, y=y_fastfetch_block)

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
    for idx, l in enumerate(langs_raw, 1):
        name = html.escape(l.get('name', 'Unknown'))
        pct = round(l.get('percent', 0), 1)
        color = l.get('color') or THEME['waka_lang_name']
        bar_w = round(370 * (pct / 100.0), 1)
        cls_idx = min(idx, 9)
        langs_svg_lines.append(f"""
      <g class="waka-bar-row waka-bar-row-{cls_idx}">
        <text x="20" y="{y_waka_curr}" class="waka-lang-name">{name}</text>
        <rect x="135" y="{y_waka_curr - 9}" width="370" height="8" rx="4" class="bar-bg" />
        <rect x="135" y="{y_waka_curr - 9}" width="{bar_w}" height="8" rx="4" fill="{color}" class="bar-fill" />
        <text x="580" y="{y_waka_curr}" text-anchor="end" class="waka-lang-val">{pct}%</text>
      </g>""")
        y_waka_curr += 22

    y_waka_curr += 15
    y_waka_lists_top = y_waka_curr

    # Tracking sets for dynamic CSS and clip definitions
    clip_defs = []
    unique_widths = set()

    # Left column: Active Editors, Operating Systems, Performance (x=20)
    y_left = y_waka_lists_top
    editors_svg = []
    y_left += 20
    for idx, ed in enumerate(editors_raw, 1):
        cls_idx = min(idx, 12)
        ed_esc = html.escape(ed)
        clip_id = f"clip-ed-{idx}"
        w = max(int(round(len(ed) * 7.2)) + 2, 12)
        unique_widths.add(w)
        clip_defs.append(f'<clipPath id="{clip_id}"><rect class="clip-stencil clip-stat-anim clip-del-{cls_idx}" x="36" y="{y_left - 12}" width="{w + 4}" height="18" /></clipPath>')
        editors_svg.append(f'''<g class="stat-row">
        <text x="20" y="{y_left}"><tspan fill="{THEME["stat_bullet"]}">●</tspan></text>
        <g clip-path="url(#{clip_id})">
          <text x="36" y="{y_left}" class="stat-item">{ed_esc}</text>
        </g>
        <line class="content-cursor cur-w-{w} cur-del-{cls_idx}" x1="36" y1="{y_left - 11}" x2="36" y2="{y_left + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      </g>''')
        y_left += 18

    y_left += 15
    y_os_header = y_left
    y_left += 20
    os_svg = []
    for idx, o in enumerate(os_raw, 1):
        cls_idx = min(idx, 12)
        o_esc = html.escape(o)
        clip_id = f"clip-waka-os-{idx}"
        w = max(int(round(len(o) * 7.2)) + 2, 12)
        unique_widths.add(w)
        clip_defs.append(f'<clipPath id="{clip_id}"><rect class="clip-stencil clip-stat-anim clip-del-{cls_idx}" x="36" y="{y_left - 12}" width="{w + 4}" height="18" /></clipPath>')
        os_svg.append(f'''<g class="stat-row">
        <text x="20" y="{y_left}"><tspan fill="{THEME["stat_bullet"]}">●</tspan></text>
        <g clip-path="url(#{clip_id})">
          <text x="36" y="{y_left}" class="stat-item">{o_esc}</text>
        </g>
        <line class="content-cursor cur-w-{w} cur-del-{cls_idx}" x1="36" y1="{y_left - 11}" x2="36" y2="{y_left + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      </g>''')
        y_left += 18

    y_left += 15
    y_perf_header = y_left
    y_left += 20
    w_time = max(int(round((len("TIME: ") + len(time_str)) * 7.2)) + 2, 12)
    w_avg = max(int(round((len("DAILY AVG: ") + len(avg_str)) * 7.2)) + 2, 12)
    unique_widths.add(w_time)
    unique_widths.add(w_avg)
    clip_defs.append(f'<clipPath id="clip-perf-1"><rect class="clip-stencil clip-stat-anim clip-del-1" x="20" y="{y_left - 12}" width="{w_time + 4}" height="18" /></clipPath>')
    clip_defs.append(f'<clipPath id="clip-perf-2"><rect class="clip-stencil clip-stat-anim clip-del-2" x="20" y="{y_left + 18 - 12}" width="{w_avg + 4}" height="18" /></clipPath>')
    perf_svg = [
        f'''<g class="stat-row">
        <g clip-path="url(#clip-perf-1)">
          <text x="20" y="{y_left}" class="stat-item"><tspan fill="{THEME["perf_time_label"]}" font-weight="bold">TIME:</tspan> <tspan id="stat-time">{html.escape(time_str)}</tspan></text>
        </g>
        <line class="content-cursor cur-w-{w_time} cur-del-1" x1="20" y1="{y_left - 11}" x2="20" y2="{y_left + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      </g>''',
        f'''<g class="stat-row">
        <g clip-path="url(#clip-perf-2)">
          <text x="20" y="{y_left + 18}" class="stat-item"><tspan fill="{THEME["perf_avg_label"]}" font-weight="bold">DAILY AVG:</tspan> <tspan id="stat-avg">{html.escape(avg_str)}</tspan></text>
        </g>
        <line class="content-cursor cur-w-{w_avg} cur-del-2" x1="20" y1="{y_left + 18 - 11}" x2="20" y2="{y_left + 18 + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      </g>'''
    ]
    y_left += 36

    # Right column: Current Projects (x=310)
    y_right = y_waka_lists_top
    projects_svg = []
    y_right += 20
    for idx, prj in enumerate(projects_raw, 1):
        cls_idx = min(idx, 12)
        prj_esc = html.escape(prj)
        clip_id = f"clip-prj-{idx}"
        w = max(int(round(len(prj) * 7.2)) + 2, 12)
        unique_widths.add(w)
        clip_defs.append(f'<clipPath id="{clip_id}"><rect class="clip-stencil clip-stat-anim clip-del-{cls_idx}" x="326" y="{y_right - 12}" width="{w + 4}" height="18" /></clipPath>')
        projects_svg.append(f'''<g class="stat-row">
        <text x="310" y="{y_right}"><tspan fill="{THEME["stat_bullet"]}">●</tspan></text>
        <g clip-path="url(#{clip_id})">
          <text x="326" y="{y_right}" class="stat-item stat-project">{prj_esc}</text>
        </g>
        <line class="content-cursor cur-w-{w} cur-del-{cls_idx}" x1="326" y1="{y_right - 11}" x2="326" y2="{y_right + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      </g>''')
        y_right += 18

    y_cursor = max(y_left, y_right) + 28

    # Section 4: Skills
    y_skills_prompt = y_cursor
    y_skills_block = y_skills_prompt + 26
    y_skills_top = y_skills_block

    # Left column skills (x=20)
    y_sk_left = y_skills_top + 20
    sk_os_svg = []
    for idx, item in enumerate(skills.get('operating_systems', []), 1):
        cls_idx = min(idx, 12)
        name_esc = html.escape(item['name'])
        clip_id = f"clip-sk-os-{idx}"
        w = max(int(round(len(item['name']) * 7.2)) + 2, 12)
        unique_widths.add(w)
        clip_defs.append(f'<clipPath id="{clip_id}"><rect class="clip-stencil clip-stat-anim clip-del-{cls_idx}" x="44" y="{y_sk_left - 12}" width="{w + 4}" height="18" /></clipPath>')
        sk_os_svg.append(f'''<g class="skill-entry">
      <image href="{item['icon']}" x="20" y="{y_sk_left - 13}" width="16" height="16" />
      <g clip-path="url(#{clip_id})">
        <text x="44" y="{y_sk_left}" class="skill-name">{name_esc}</text>
      </g>
      <line class="content-cursor cur-w-{w} cur-del-{cls_idx}" x1="44" y1="{y_sk_left - 11}" x2="44" y2="{y_sk_left + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
    </g>''')
        y_sk_left += 22

    y_sk_left += 15
    y_sk_ed_header = y_sk_left
    y_sk_left += 20
    sk_ed_svg = []
    for idx, item in enumerate(skills.get('editors', []), 1):
        cls_idx = min(idx, 12)
        name_esc = html.escape(item['name'])
        clip_id = f"clip-sk-ed-{idx}"
        w = max(int(round(len(item['name']) * 7.2)) + 2, 12)
        unique_widths.add(w)
        clip_defs.append(f'<clipPath id="{clip_id}"><rect class="clip-stencil clip-stat-anim clip-del-{cls_idx}" x="44" y="{y_sk_left - 12}" width="{w + 4}" height="18" /></clipPath>')
        sk_ed_svg.append(f'''<g class="skill-entry">
      <image href="{item['icon']}" x="20" y="{y_sk_left - 13}" width="16" height="16" />
      <g clip-path="url(#{clip_id})">
        <text x="44" y="{y_sk_left}" class="skill-name">{name_esc}</text>
      </g>
      <line class="content-cursor cur-w-{w} cur-del-{cls_idx}" x1="44" y1="{y_sk_left - 11}" x2="44" y2="{y_sk_left + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
    </g>''')
        y_sk_left += 22

    # Right column skills (x=310)
    y_sk_right = y_skills_top + 20
    sk_de_svg = []
    for idx, item in enumerate(skills.get('desktop_environments', []), 1):
        cls_idx = min(idx, 12)
        name_esc = html.escape(item['name'])
        clip_id = f"clip-sk-de-{idx}"
        w = max(int(round(len(item['name']) * 7.2)) + 2, 12)
        unique_widths.add(w)
        clip_defs.append(f'<clipPath id="{clip_id}"><rect class="clip-stencil clip-stat-anim clip-del-{cls_idx}" x="334" y="{y_sk_right - 12}" width="{w + 4}" height="18" /></clipPath>')
        sk_de_svg.append(f'''<g class="skill-entry">
      <image href="{item['icon']}" x="310" y="{y_sk_right - 13}" width="16" height="16" />
      <g clip-path="url(#{clip_id})">
        <text x="334" y="{y_sk_right}" class="skill-name">{name_esc}</text>
      </g>
      <line class="content-cursor cur-w-{w} cur-del-{cls_idx}" x1="334" y1="{y_sk_right - 11}" x2="334" y2="{y_sk_right + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
    </g>''')
        y_sk_right += 22

    y_sk_right += 15
    y_sk_lt_header = y_sk_right
    y_sk_right += 20
    sk_lt_svg = []
    for idx, item in enumerate(skills.get('languages_tools', []), 1):
        cls_idx = min(idx, 12)
        name_esc = html.escape(item['name'])
        clip_id = f"clip-sk-lt-{idx}"
        w = max(int(round(len(item['name']) * 7.2)) + 2, 12)
        unique_widths.add(w)
        clip_defs.append(f'<clipPath id="{clip_id}"><rect class="clip-stencil clip-stat-anim clip-del-{cls_idx}" x="334" y="{y_sk_right - 12}" width="{w + 4}" height="18" /></clipPath>')
        sk_lt_svg.append(f'''<g class="skill-entry">
      <image href="{item['icon']}" x="310" y="{y_sk_right - 13}" width="16" height="16" />
      <g clip-path="url(#{clip_id})">
        <text x="334" y="{y_sk_right}" class="skill-name">{name_esc}</text>
      </g>
      <line class="content-cursor cur-w-{w} cur-del-{cls_idx}" x1="334" y1="{y_sk_right - 11}" x2="334" y2="{y_sk_right + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
    </g>''')
        y_sk_right += 22

    y_cursor = max(y_sk_left, y_sk_right) + 28

    # Section 5: Bottom cursor and footer
    y_final_prompt = y_cursor
    total_height = y_final_prompt + 55
    y_footer = total_height - 12

    # Section Headers (9 headers)
    # Header format: (id_suffix, raw_title, display_title, x, y, font_size, css_class, width)
    header_configs = [
        ('lang', 'LANGUAGES', 'LANGUAGES', 20, y_waka_block, 14, 'section-title', 76),
        ('editors', 'ACTIVE EDITORS', 'ACTIVE EDITORS', 20, y_waka_lists_top, 14, 'section-title', 118),
        ('os', 'OPERATING SYSTEMS', 'OPERATING SYSTEMS', 20, y_os_header, 14, 'section-title', 143),
        ('perf', 'aldrin@frtzhahn performance', 'aldrin@frtzhahn performance', 20, y_perf_header, 14, 'section-title', 227),
        ('projects', 'CURRENT PROJECTS', 'CURRENT PROJECTS', 310, y_waka_lists_top, 14, 'section-title', 135),
        ('sk-os', 'OPERATING SYSTEMS', 'OPERATING SYSTEMS', 20, y_skills_top, 13, 'skills-hdr', 133),
        ('sk-ed', 'EDITORS & IDES', 'EDITORS &amp; IDES', 20, y_sk_ed_header, 13, 'skills-hdr', 110),
        ('sk-de', 'DESKTOP ENVIRONMENTS', 'DESKTOP ENVIRONMENTS', 310, y_skills_top, 13, 'skills-hdr', 156),
        ('sk-lt', 'LANGUAGES/TOOLS', 'LANGUAGES/TOOLS', 310, y_sk_lt_header, 13, 'skills-hdr', 117),
    ]

    header_clips = []
    header_css = []
    for hid, rtitle, dtitle, hx, hy, hfs, hcls, hw in header_configs:
        y_rect = hy - (15 if hfs == 14 else 14)
        header_clips.append(f'<clipPath id="clip-hdr-{hid}"><rect class="clip-stencil clip-hdr-anim" x="{hx}" y="{y_rect}" width="{hw + 4}" height="22" /></clipPath>')
        header_css.append(f'''    .cur-hdr-{hid} {{ animation: cur-hdr-{hid} 10s forwards; }}
    @keyframes cur-hdr-{hid} {{
      0%, 18.0% {{ transform: translateX(0); opacity: 0; }}
      18.5% {{ opacity: 1; }}
      45.0% {{ transform: translateX({hw}px); opacity: 1; }}
      45.5%, 100% {{ transform: translateX({hw}px); opacity: 0; }}
    }}''')

    # Generate dynamic CSS for stat and skill cursors
    dynamic_css_lines = []
    for w in sorted(unique_widths):
        dynamic_css_lines.append(f"""    .cur-w-{w} {{ animation: cur-anim-{w} 10s forwards; }}
    @keyframes cur-anim-{w} {{
      0%, 20.0% {{ transform: translateX(0); opacity: 0; }}
      20.5% {{ opacity: 1; }}
      55.0% {{ transform: translateX({w}px); opacity: 1; }}
      55.5%, 100% {{ transform: translateX({w}px); opacity: 0; }}
    }}""")

    for i in range(1, 13):
        d = round(0.08 * i, 2)
        dynamic_css_lines.append(f"    .clip-del-{i} {{ animation-delay: {d}s; }}")
        dynamic_css_lines.append(f"    .cur-del-{i}  {{ animation-delay: {d}s; }}")

    dynamic_stat_css = "\n".join(dynamic_css_lines)
    header_css_str = "\n".join(header_css)
    all_clip_defs_str = "\n    ".join(clip_defs)
    header_clips_str = "\n    ".join(header_clips)

    # ---------------- SVG Assembly ----------------
    svg_out = f"""<svg viewBox="0 0 600 {total_height}" width="600" height="{total_height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Typewriter Command Clip Paths (Using scaleX for 100% WebKit hardware compatibility) -->
    <clipPath id="clip-fastfetch">
      <rect class="clip-stencil clip-fastfetch-anim" x="180" y="{y_fastfetch_prompt - 16}" width="80" height="24" />
    </clipPath>
    <clipPath id="clip-cat">
      <rect class="clip-stencil clip-cat-anim" x="180" y="{y_bio_prompt - 16}" width="140" height="24" />
    </clipPath>
    <clipPath id="clip-htop">
      <rect class="clip-stencil clip-htop-anim" x="180" y="{y_waka_prompt - 16}" width="105" height="24" />
    </clipPath>
    <clipPath id="clip-skills">
      <rect class="clip-stencil clip-skills-anim" x="180" y="{y_skills_prompt - 16}" width="140" height="24" />
    </clipPath>

    <!-- Bio Sequential Line Clip Paths -->
    <clipPath id="clip-bio-1">
      <rect class="clip-stencil clip-bio1-anim" x="20" y="{y_bio_1 - 14}" width="275" height="20" />
    </clipPath>
    <clipPath id="clip-bio-2">
      <rect class="clip-stencil clip-bio2-anim" x="20" y="{y_bio_2 - 14}" width="305" height="20" />
    </clipPath>
    <clipPath id="clip-bio-3">
      <rect class="clip-stencil clip-bio3-anim" x="20" y="{y_bio_3 - 14}" width="260" height="20" />
    </clipPath>

    <!-- Fastfetch Course and Traits Clip Paths -->
    <clipPath id="clip-course">
      <rect class="clip-stencil clip-course-anim" x="160" y="{y_fastfetch_block + 96 - 14}" width="324" height="20" />
    </clipPath>
    <clipPath id="clip-traits">
      <rect class="clip-stencil clip-traits-anim" x="160" y="{y_fastfetch_block + 116 - 14}" width="300" height="20" />
    </clipPath>

    <!-- Section and Category Header Clip Paths -->
    {header_clips_str}

    <!-- Content Items Dynamic Clip Paths -->
    {all_clip_defs_str}
  </defs>

  <style>
    /* Typography and Base Styles */
    text {{
      font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'DejaVu Sans Mono', monospace;
      dominant-baseline: alphabetic;
    }}

    .prompt-host {{ fill: {THEME['prompt_host']}; font-size: 14px; }}
    .prompt-colon {{ fill: {THEME['prompt_colon']}; font-size: 14px; }}
    .prompt-dir   {{ fill: {THEME['prompt_dir']}; font-weight: bold; font-size: 14px; }}
    .prompt-char  {{ fill: {THEME['prompt_colon']}; font-size: 14px; }}
    .cmd-text     {{ fill: {THEME['cmd']}; font-size: 14px; }}

    .cmd-cursor {{
      fill: {THEME['cursor']};
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

    /* Content Aqua Vertical Cursor */
    .content-cursor {{
      opacity: 0;
    }}

    /* Command Typography / Typewriter Stencils and Cursor Synchronizers (Smooth Linear Entrance: 10s) */
    .clip-fastfetch-anim {{ animation: type-fastfetch 10s forwards; }}
    .cursor-fastfetch-anim {{ animation: cursor-fastfetch 10s forwards; }}

    .clip-cat-anim       {{ animation: type-cat 10s forwards; }}
    .cursor-cat-anim     {{ animation: cursor-cat 10s forwards; }}

    .clip-htop-anim      {{ animation: type-htop 10s forwards; }}
    .cursor-htop-anim    {{ animation: cursor-htop 10s forwards; }}

    .clip-skills-anim    {{ animation: type-skills 10s forwards; }}
    .cursor-skills-anim  {{ animation: cursor-skills 10s forwards; }}

    @keyframes type-fastfetch {{
      0% {{ transform: scaleX(0); }}
      24.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cursor-fastfetch {{
      0% {{ transform: translateX(-76px); }}
      24.0%, 100% {{ transform: translateX(0); }}
    }}

    @keyframes type-cat {{
      0% {{ transform: scaleX(0); }}
      24.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cursor-cat {{
      0% {{ transform: translateX(-135px); }}
      24.0%, 100% {{ transform: translateX(0); }}
    }}

    @keyframes type-htop {{
      0% {{ transform: scaleX(0); }}
      24.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cursor-htop {{
      0% {{ transform: translateX(-101px); }}
      24.0%, 100% {{ transform: translateX(0); }}
    }}

    @keyframes type-skills {{
      0% {{ transform: scaleX(0); }}
      24.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cursor-skills {{
      0% {{ transform: translateX(-135px); }}
      24.0%, 100% {{ transform: translateX(0); }}
    }}

    /* Bio Sequential Keyframes with Synchronized Aqua Cursor */
    .clip-bio1-anim {{ animation: type-bio-1 10s forwards; }}
    .cursor-bio1-anim {{ animation: cur-bio-1 10s forwards; }}
    @keyframes type-bio-1 {{
      0%, 18.0% {{ transform: scaleX(0); }}
      44.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cur-bio-1 {{
      0%, 18.0% {{ transform: translateX(0); opacity: 0; }}
      18.5% {{ opacity: 1; }}
      44.0% {{ transform: translateX(265px); opacity: 1; }}
      44.5%, 100% {{ transform: translateX(265px); opacity: 0; }}
    }}

    .clip-bio2-anim {{ animation: type-bio-2 10s forwards; }}
    .cursor-bio2-anim {{ animation: cur-bio-2 10s forwards; }}
    @keyframes type-bio-2 {{
      0%, 44.0% {{ transform: scaleX(0); }}
      70.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cur-bio-2 {{
      0%, 44.0% {{ transform: translateX(0); opacity: 0; }}
      44.5% {{ opacity: 1; }}
      70.0% {{ transform: translateX(295px); opacity: 1; }}
      70.5%, 100% {{ transform: translateX(295px); opacity: 0; }}
    }}

    .clip-bio3-anim {{ animation: type-bio-3 10s forwards; }}
    .cursor-bio3-anim {{ animation: cur-bio-3 10s forwards; }}
    @keyframes type-bio-3 {{
      0%, 70.0% {{ transform: scaleX(0); }}
      94.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cur-bio-3 {{
      0%, 70.0% {{ transform: translateX(0); opacity: 0; }}
      70.5% {{ opacity: 1; }}
      94.0% {{ transform: translateX(250px); opacity: 1; }}
      94.5%, 100% {{ transform: translateX(250px); opacity: 0; }}
    }}

    /* Fastfetch Course and Traits Sequential Keyframes with Aqua Cursor */
    .clip-course-anim {{ animation: type-course 10s forwards; }}
    .cursor-course-anim {{ animation: cur-course 10s forwards; }}
    @keyframes type-course {{
      0%, 18.0% {{ transform: scaleX(0); }}
      44.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cur-course {{
      0%, 18.0% {{ transform: translateX(0); opacity: 0; }}
      18.5% {{ opacity: 1; }}
      44.0% {{ transform: translateX(320px); opacity: 1; }}
      44.5%, 100% {{ transform: translateX(320px); opacity: 0; }}
    }}

    .clip-traits-anim {{ animation: type-traits 10s forwards; }}
    .cursor-traits-anim {{ animation: cur-traits 10s forwards; }}
    @keyframes type-traits {{
      0%, 44.0% {{ transform: scaleX(0); }}
      70.0%, 100% {{ transform: scaleX(1); }}
    }}
    @keyframes cur-traits {{
      0%, 44.0% {{ transform: translateX(0); opacity: 0; }}
      44.5% {{ opacity: 1; }}
      70.0% {{ transform: translateX(285px); opacity: 1; }}
      70.5%, 100% {{ transform: translateX(285px); opacity: 0; }}
    }}

    /* Section and Category Headers Typewriter Keyframes */
    .clip-hdr-anim {{ animation: type-header 10s forwards; }}
    @keyframes type-header {{
      0%, 18.0% {{ transform: scaleX(0); }}
      45.0%, 100% {{ transform: scaleX(1); }}
    }}
{header_css_str}

    /* Output Fades (Fastfetch, Bio, Waka, Skills) */
    .output-fade {{
      animation: output-fade-anim 10s forwards;
    }}
    @keyframes output-fade-anim {{
      0%, 14.0% {{ opacity: 0; }}
      35.0%, 100% {{ opacity: 1; }}
    }}

    /* Progress Bar Fills (One-Shot: 18-55%) */
    .bar-bg {{ fill: {THEME['bar_bg']}; }}
    .bar-fill {{
      transform-box: fill-box;
      transform-origin: left;
      animation: fill-bar-anim 10s forwards;
    }}
    @keyframes fill-bar-anim {{
      0%, 18.0% {{ transform: scaleX(0); }}
      55.0%, 100% {{ transform: scaleX(1); }}
    }}

    /* WakaTime Bar Rows - Staggered Cascade Entrance (One-Shot: 20-70%) */
    .waka-bar-row {{
      animation: fade-row 10s forwards;
    }}
    @keyframes fade-row {{
      0%, 20.0% {{ opacity: 0; transform: translateX(-10px); }}
      70.0%, 100% {{ opacity: 1; transform: translateX(0); }}
    }}
    .waka-bar-row-1 {{ animation-delay: 0.1s; }}
    .waka-bar-row-2 {{ animation-delay: 0.2s; }}
    .waka-bar-row-3 {{ animation-delay: 0.3s; }}
    .waka-bar-row-4 {{ animation-delay: 0.4s; }}
    .waka-bar-row-5 {{ animation-delay: 0.5s; }}
    .waka-bar-row-6 {{ animation-delay: 0.6s; }}
    .waka-bar-row-7 {{ animation-delay: 0.7s; }}
    .waka-bar-row-8 {{ animation-delay: 0.8s; }}
    .waka-bar-row-9 {{ animation-delay: 0.9s; }}

    /* Stat and Skill Content Items Smooth Typewriter Stencil */
    .clip-stat-anim {{
      animation: type-stat-clip 10s forwards;
    }}
    @keyframes type-stat-clip {{
      0%, 20.0% {{ transform: scaleX(0); }}
      55.0%, 100% {{ transform: scaleX(1); }}
    }}

    /* Dynamic Content Cursor Animations and Staggered Ripple Delays */
{dynamic_stat_css}

    /* Fastfetch Styles */
    .ff-spec-label {{ fill: {THEME['fastfetch_spec_label']}; font-size: 11px; }}
    .ff-spec-val   {{ fill: {THEME['fg']}; font-size: 11px; }}
    .ff-course-hdr {{ fill: {THEME['fastfetch_course_hdr']}; font-weight: bold; font-size: 11px; }}
    .ff-course-val {{ fill: {THEME['fg']}; font-size: 11px; }}

    /* Bio Styles */
    .bio-line   {{ fill: {THEME['bio_line']}; font-size: 12px; }}
    .bio-accent {{ fill: {THEME['bio_accent']}; font-weight: bold; font-size: 12px; }}

    /* WakaTime Styles */
    .section-title {{ fill: {THEME['section_title']}; font-size: 14px; font-weight: bold; text-transform: uppercase; }}
    .waka-lang-name {{ fill: {THEME['waka_lang_name']}; font-size: 11px; }}
    .waka-lang-val  {{ fill: {THEME['fg']}; font-size: 11px; }}
    .stat-item      {{ fill: {THEME['fg']}; font-size: 12px; }}
    .stat-project   {{ fill: {THEME['stat_project']}; }}

    /* Skills Styles */
    .skills-hdr  {{ fill: {THEME['skills_hdr']}; font-size: 13px; font-weight: bold; text-transform: uppercase; }}
    .skill-name  {{ fill: {THEME['fg']}; font-size: 12px; }}

    /* Footer */
    .footer-text {{ fill: {THEME['footer_text']}; font-size: 10px; }}
    .footer-en-cours {{ fill: {THEME['footer_badge']}; font-size: 10px; font-weight: bold; }}

    /* Reduced Motion Accessibility */
    @media (prefers-reduced-motion: reduce) {{
      * {{
        animation: none !important;
      }}
      .output-fade, .waka-bar-row, .stat-item, .skill-entry, .info-line, .skills-hdr, .section-title {{
        opacity: 1 !important;
        transform: none !important;
      }}
      .clip-stencil, .bar-fill {{
        transform: none !important;
      }}
      .content-cursor {{
        display: none !important;
      }}
    }}
  </style>

  <!-- Window Frame Background -->
  <rect x="0.5" y="0.5" width="599" height="{total_height - 1}" rx="6" fill="{THEME['bg']}" stroke="{THEME['border']}" />

  <!-- Window Header -->
  <path d="M0.5 6.5A6 6 0 0 1 6.5 0.5H593.5A6 6 0 0 1 599.5 6.5V30.5H0.5Z" fill="{THEME['header_bg']}" />
  <line x1="0" y1="30.5" x2="600" y2="30.5" stroke="{THEME['border']}" />

  <!-- macOS Window Controls (Commented out: Uncomment to restore)
  <circle cx="21" cy="15.5" r="5" fill="{THEME['dot_red']}" />
  <circle cx="37" cy="15.5" r="5" fill="{THEME['dot_yellow']}" />
  <circle cx="53" cy="15.5" r="5" fill="{THEME['dot_green']}" />
  -->

  <!-- Linux Terminal Tab and Window Header (Kitty / Sway Rice) -->
  <g id="window-header-linux">
    <!-- Active Tab -->
    <rect x="12" y="4" width="125" height="26.5" rx="4" fill="{THEME['tab_bg']}" />
    <line x1="12" y1="30.5" x2="137" y2="30.5" stroke="{THEME['tab_accent']}" stroke-width="2" />
    <text x="20" y="20" fill="{THEME['tab_accent']}" font-size="11" font-weight="bold">&gt;_</text>
    <text x="38" y="20" fill="{THEME['fg']}" font-size="11" font-weight="bold">1: zsh (~)</text>
    <!-- New Tab (+) -->
    <text x="148" y="20" fill="{THEME['fg_subtle']}" font-size="13">+</text>
    <!-- Centered Host/Session Title -->
    <text x="310" y="20" text-anchor="middle" fill="{THEME['fg_muted']}" font-size="11">aldrin@frtzhahn: ~</text>
    <!-- Obsidian-style Window Controls (slots: 500-532, 532-564, 564-596) -->
    <g id="window-controls-obsidian">
      <!-- Minimize: centered at x=516, y=15.5 -->
      <line x1="511" y1="15.5" x2="521" y2="15.5" stroke="{THEME['fg_subtle']}" stroke-width="1.2" stroke-linecap="round" />
      <!-- Maximize: centered at x=548, y=15.5 -->
      <rect x="543" y="10.5" width="10" height="10" rx="1.5" fill="none" stroke="{THEME['fg_subtle']}" stroke-width="1.2" />
      <!-- Close: centered at x=580, y=15.5 -->
      <path d="M575.5 11 L584.5 20 M584.5 11 L575.5 20" stroke="{THEME['fg_subtle']}" stroke-width="1.2" stroke-linecap="round" />
    </g>
  </g>

  <!-- ==================== 1. FASTFETCH ==================== -->
  <g id="fastfetch-section">
    <g id="fastfetch-prompt-line">
      <text x="20" y="{y_fastfetch_prompt}" xml:space="preserve"><tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan></text>
      <g clip-path="url(#clip-fastfetch)">
        <text x="180" y="{y_fastfetch_prompt}" class="cmd-text">fastfetch</text>
      </g>
      <g class="cursor-fastfetch-anim">
        <text x="256" y="{y_fastfetch_prompt}" class="cmd-cursor" dy="-2">_</text>
      </g>
    </g>

    <g class="output-fade">
      <!-- Mocha Avatar -->
      <g id="fastfetch-avatar">
        {mocha_mascot_svg}
      </g>

      <!-- System Specs -->
      <g id="fastfetch-specs">
        <!-- pull_requests -->
        <text x="160" y="{y_fastfetch_block + 18}" class="ff-spec-label">pull_requests</text>
        <rect x="255" y="{y_fastfetch_block + 10}" width="190" height="8" rx="4" class="bar-bg" />
        <rect x="255" y="{y_fastfetch_block + 10}" width="{pr_bar_w}" height="8" rx="4" fill="{THEME['pr_bar']}" class="bar-fill" />
        <text x="570" y="{y_fastfetch_block + 18}" text-anchor="end" class="ff-spec-val">{pr_str}</text>

        <!-- issues_solved -->
        <text x="160" y="{y_fastfetch_block + 40}" class="ff-spec-label">issues_solved</text>
        <rect x="255" y="{y_fastfetch_block + 32}" width="190" height="8" rx="4" class="bar-bg" />
        <rect x="255" y="{y_fastfetch_block + 32}" width="{issue_bar_w}" height="8" rx="4" fill="{THEME['issue_bar']}" class="bar-fill" />
        <text x="570" y="{y_fastfetch_block + 40}" text-anchor="end" class="ff-spec-val">{issue_str}</text>

        <!-- commit_streak -->
        <text x="160" y="{y_fastfetch_block + 62}" class="ff-spec-label">commit_streak</text>
        <rect x="255" y="{y_fastfetch_block + 54}" width="190" height="8" rx="4" class="bar-bg" />
        <rect x="255" y="{y_fastfetch_block + 54}" width="{streak_bar_w}" height="8" rx="4" fill="{THEME['streak_bar']}" class="bar-fill" />
        <text x="570" y="{y_fastfetch_block + 62}" text-anchor="end" class="ff-spec-val">{streak_str}</text>

        <line x1="160" y1="{y_fastfetch_block + 78}" x2="570" y2="{y_fastfetch_block + 78}" stroke="{THEME['border']}" stroke-dasharray="4,4" />

        <!-- Course & Traits -->
        <g clip-path="url(#clip-course)">
          <text x="160" y="{y_fastfetch_block + 96}"><tspan class="ff-course-hdr">COURSE</tspan><tspan class="ff-course-val">: Bachelor of Science in Computer Science</tspan></text>
        </g>
        <line class="content-cursor cursor-course-anim" x1="160" y1="{y_fastfetch_block + 96 - 10}" x2="160" y2="{y_fastfetch_block + 96 + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />

        <g clip-path="url(#clip-traits)">
          <text x="160" y="{y_fastfetch_block + 116}"><tspan class="ff-course-hdr">TRAITS</tspan><tspan class="ff-course-val">: Procrastinator, Crammer, Night Owl</tspan></text>
        </g>
        <line class="content-cursor cursor-traits-anim" x1="160" y1="{y_fastfetch_block + 116 - 10}" x2="160" y2="{y_fastfetch_block + 116 + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      </g>
    </g>
  </g>

  <!-- ==================== 2. BIO ==================== -->
  <g id="bio-section">
    <g id="bio-prompt-line">
      <text x="20" y="{y_bio_prompt}" xml:space="preserve"><tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan></text>
      <g clip-path="url(#clip-cat)">
        <text x="180" y="{y_bio_prompt}" class="cmd-text">cat about_me.txt</text>
      </g>
      <g class="cursor-cat-anim">
        <text x="315" y="{y_bio_prompt}" class="cmd-cursor" dy="-2">_</text>
      </g>
    </g>

    <g class="output-fade">
      <g clip-path="url(#clip-bio-1)">
        <text x="20" y="{y_bio_1}" xml:space="preserve"><tspan class="bio-line">&gt; Hello, I'm </tspan><tspan class="bio-accent">Aldrin James A. Alciso</tspan></text>
      </g>
      <line class="content-cursor cursor-bio1-anim" x1="20" y1="{y_bio_1 - 11}" x2="20" y2="{y_bio_1 + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />

      <g clip-path="url(#clip-bio-2)">
        <text x="20" y="{y_bio_2}" xml:space="preserve"><tspan class="bio-line">&gt; Student at </tspan><tspan class="bio-accent">University of Caloocan City</tspan></text>
      </g>
      <line class="content-cursor cursor-bio2-anim" x1="20" y1="{y_bio_2 - 11}" x2="20" y2="{y_bio_2 + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />

      <g clip-path="url(#clip-bio-3)">
        <text x="20" y="{y_bio_3}" xml:space="preserve"><tspan class="bio-line">&gt; Exploring new things everyday :3</tspan></text>
      </g>
      <line class="content-cursor cursor-bio3-anim" x1="20" y1="{y_bio_3 - 11}" x2="20" y2="{y_bio_3 + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
    </g>
  </g>

  <!-- ==================== 3. WAKATIME ==================== -->
  <g id="wakatime-section">
    <g id="wakatime-prompt-line">
      <text x="20" y="{y_waka_prompt}" xml:space="preserve"><tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan></text>
      <g clip-path="url(#clip-htop)">
        <text x="180" y="{y_waka_prompt}" class="cmd-text">htop --stats</text>
      </g>
      <g class="cursor-htop-anim">
        <text x="281" y="{y_waka_prompt}" class="cmd-cursor" dy="-2">_</text>
      </g>
    </g>

    <g class="output-fade">
      <!-- Languages Section -->
      <g clip-path="url(#clip-hdr-lang)">
        <text x="20" y="{y_waka_block}" class="section-title">LANGUAGES</text>
      </g>
      <line class="content-cursor cur-hdr-lang" x1="20" y1="{y_waka_block - 13}" x2="20" y2="{y_waka_block + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="20" y1="{y_waka_block + 6}" x2="580" y2="{y_waka_block + 6}" stroke="{THEME['divider']}" />
      <!-- LANG_START -->
{''.join(langs_svg_lines)}
      <!-- LANG_END -->

      <!-- Left Column: Active Editors, OS, Performance -->
      <!-- Editors -->
      <g clip-path="url(#clip-hdr-editors)">
        <text x="20" y="{y_waka_lists_top}" class="section-title">ACTIVE EDITORS</text>
      </g>
      <line class="content-cursor cur-hdr-editors" x1="20" y1="{y_waka_lists_top - 13}" x2="20" y2="{y_waka_lists_top + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="20" y1="{y_waka_lists_top + 6}" x2="280" y2="{y_waka_lists_top + 6}" stroke="{THEME['divider']}" />
      <!-- EDITORS_START -->
      {''.join(editors_svg)}
      <!-- EDITORS_END -->

      <!-- OS -->
      <g clip-path="url(#clip-hdr-os)">
        <text x="20" y="{y_os_header}" class="section-title">OPERATING SYSTEMS</text>
      </g>
      <line class="content-cursor cur-hdr-os" x1="20" y1="{y_os_header - 13}" x2="20" y2="{y_os_header + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="20" y1="{y_os_header + 6}" x2="280" y2="{y_os_header + 6}" stroke="{THEME['divider']}" />
      <!-- OS_START -->
      {''.join(os_svg)}
      <!-- OS_END -->

      <!-- Performance -->
      <g clip-path="url(#clip-hdr-perf)">
        <text x="20" y="{y_perf_header}" class="section-title">aldrin@frtzhahn performance</text>
      </g>
      <line class="content-cursor cur-hdr-perf" x1="20" y1="{y_perf_header - 13}" x2="20" y2="{y_perf_header + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="20" y1="{y_perf_header + 6}" x2="280" y2="{y_perf_header + 6}" stroke="{THEME['divider']}" />
      {''.join(perf_svg)}

      <!-- Right Column: Current Projects -->
      <g clip-path="url(#clip-hdr-projects)">
        <text x="310" y="{y_waka_lists_top}" class="section-title">CURRENT PROJECTS</text>
      </g>
      <line class="content-cursor cur-hdr-projects" x1="310" y1="{y_waka_lists_top - 13}" x2="310" y2="{y_waka_lists_top + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="310" y1="{y_waka_lists_top + 6}" x2="580" y2="{y_waka_lists_top + 6}" stroke="{THEME['divider']}" />
      <!-- PROJECTS_START -->
      {''.join(projects_svg)}
      <!-- PROJECTS_END -->
    </g>
  </g>

  <!-- ==================== 4. SKILLS ==================== -->
  <g id="skills-section">
    <g id="skills-prompt-line">
      <text x="20" y="{y_skills_prompt}" xml:space="preserve"><tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan></text>
      <g clip-path="url(#clip-skills)">
        <text x="180" y="{y_skills_prompt}" class="cmd-text">cat ~/skills.txt</text>
      </g>
      <g class="cursor-skills-anim">
        <text x="315" y="{y_skills_prompt}" class="cmd-cursor" dy="-2">_</text>
      </g>
    </g>

    <g class="output-fade">
      <!-- Left Column Skills -->
      <g clip-path="url(#clip-hdr-sk-os)">
        <text x="20" y="{y_skills_top}" class="skills-hdr">OPERATING SYSTEMS</text>
      </g>
      <line class="content-cursor cur-hdr-sk-os" x1="20" y1="{y_skills_top - 12}" x2="20" y2="{y_skills_top + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="20" y1="{y_skills_top + 6}" x2="280" y2="{y_skills_top + 6}" stroke="{THEME['divider']}" />
      {''.join(sk_os_svg)}

      <g clip-path="url(#clip-hdr-sk-ed)">
        <text x="20" y="{y_sk_ed_header}" class="skills-hdr">EDITORS &amp; IDES</text>
      </g>
      <line class="content-cursor cur-hdr-sk-ed" x1="20" y1="{y_sk_ed_header - 12}" x2="20" y2="{y_sk_ed_header + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="20" y1="{y_sk_ed_header + 6}" x2="280" y2="{y_sk_ed_header + 6}" stroke="{THEME['divider']}" />
      {''.join(sk_ed_svg)}

      <!-- Right Column Skills -->
      <g clip-path="url(#clip-hdr-sk-de)">
        <text x="310" y="{y_skills_top}" class="skills-hdr">DESKTOP ENVIRONMENTS</text>
      </g>
      <line class="content-cursor cur-hdr-sk-de" x1="310" y1="{y_skills_top - 12}" x2="310" y2="{y_skills_top + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="310" y1="{y_skills_top + 6}" x2="580" y2="{y_skills_top + 6}" stroke="{THEME['divider']}" />
      {''.join(sk_de_svg)}

      <g clip-path="url(#clip-hdr-sk-lt)">
        <text x="310" y="{y_sk_lt_header}" class="skills-hdr">LANGUAGES/TOOLS</text>
      </g>
      <line class="content-cursor cur-hdr-sk-lt" x1="310" y1="{y_sk_lt_header - 12}" x2="310" y2="{y_sk_lt_header + 2}" stroke="{THEME['content_cursor']}" stroke-width="1.8" />
      <line x1="310" y1="{y_sk_lt_header + 6}" x2="580" y2="{y_sk_lt_header + 6}" stroke="{THEME['divider']}" />
      {''.join(sk_lt_svg)}
    </g>
  </g>

  <!-- ==================== 5. FOOTER ==================== -->
  <g id="footer-section">
    <text x="20" y="{y_final_prompt}" xml:space="preserve"><tspan class="prompt-host">aldrin@frtzhahn</tspan><tspan class="prompt-colon">:</tspan><tspan class="prompt-dir">~</tspan><tspan class="prompt-char">$ </tspan><tspan class="cmd-cursor" dy="-2">_</tspan></text>

    <line x1="0" y1="{total_height - 28}" x2="600" y2="{total_height - 28}" stroke="{THEME['divider']}" />
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
    gh_stats = fetch_github_stats()
    print(f"GitHub Stats: PRs={gh_stats.get('pr_str')}, Issues={gh_stats.get('issue_str')}, Streak={gh_stats.get('streak_str')}")

    svg_content, total_height = generate_native_profile_svg(stats, skills, gh_stats)

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
