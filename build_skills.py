import urllib.request
import base64
import json

slugs = {
    'Arch WSL': ('archlinux', '#1793d1'),
    'CachyOS': ('archlinux', '#13e098'),
    'Windows 10': ('windows11', '#0078d6'),
    'Android': ('android', '#3DDC84'),
    'Kali Linux': ('kalilinux', '#557C94'),
    'KDE': ('kde', '#1D99F3'),
    'GNOME': ('gnome', '#4A86CF'),
    'Sway': ('sway', '#333333'),
    'i3': ('i3', '#4C7899'),
    'GlazeWM': ('windows11', '#ffffff'),
    'VSCode': ('visualstudiocode', '#007ACC'),
    'Vim': ('vim', '#019733'),
    'Neovim': ('neovim', '#57A143'),
    'IDEA': ('intellijidea', '#000000'),
    'Arduino': ('arduino', '#00979D'),
    'Obsidian': ('obsidian', '#483699'),
    'C': ('c', '#A8B9CC'),
    'CSS': ('css3', '#1572B6'),
    'HTML5': ('html5', '#E34F26'),
    'JavaScript': ('javascript', '#F7DF1E'),
    'Canva': ('canva', '#00C4CC'),
    'Git': ('git', '#F05032'),
    'Java': ('java', '#007396'), # Fallback
    'Figma': ('figma', '#F24E1E'),
    'Maven': ('apachemaven', '#C71A22'),
    'JavaFX': ('java', '#007396'), # Fallback
}

def get_b64(slug, color):
    url = f"https://cdn.simpleicons.org/{slug}/{color[1:]}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            svg_data = response.read()
            return f"data:image/svg+xml;base64,{base64.b64encode(svg_data).decode()}"
    except Exception:
        fallback = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="{color}"/></svg>'
        return f"data:image/svg+xml;base64,{base64.b64encode(fallback.encode()).decode()}"

# Fetch icons
print("Fetching icons...")
icons = {}
for name, (slug, color) in slugs.items():
    icons[name] = get_b64(slug, color)

structure = [
    ("├── ", "Operating Systems", True, [
        ("│   ├── ", "Arch WSL"),
        ("│   ├── ", "CachyOS"),
        ("│   ├── ", "Windows 10"),
        ("│   ├── ", "Android"),
        ("│   └── ", "Kali Linux"),
    ]),
    ("├── ", "Desktop Environments", True, [
        ("│   ├── ", "KDE"),
        ("│   ├── ", "GNOME"),
        ("│   ├── ", "Sway"),
        ("│   ├── ", "i3"),
        ("│   └── ", "GlazeWM"),
    ]),
    ("├── ", "Editors &amp; IDEs", True, [
        ("│   ├── ", "VSCode"),
        ("│   ├── ", "Vim"),
        ("│   ├── ", "Neovim"),
        ("│   ├── ", "IDEA"),
        ("│   ├── ", "Arduino"),
        ("│   └── ", "Obsidian"),
    ]),
    ("└── ", "Languages &amp; Tools", True, [
        ("    ├── ", "C"),
        ("    ├── ", "Java"),
        ("    ├── ", "JavaScript"),
        ("    ├── ", "HTML5"),
        ("    ├── ", "CSS"),
        ("    ├── ", "Git"),
        ("    ├── ", "Maven"),
        ("    ├── ", "JavaFX"),
        ("    ├── ", "Figma"),
        ("    └── ", "Canva"),
    ])
]

lines_html = ""
for item in structure:
    prefix, name, is_dir, children = item
    lines_html += f'<div><span class="tree-line">{prefix}</span><span class="dir">{name}</span></div>\n'
    for c_prefix, c_name in children:
        b64 = icons[c_name]
        lines_html += f'<div><span class="tree-line">{c_prefix}</span><span class="item"><img class="icon" src="{b64}"/> <span class="file">{c_name}</span></span></div>\n'

svg_template = f"""<svg fill="none" viewBox="0 0 600 580" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="100%" height="100%">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <style>
        .container {{
          background-color: #1a1b26;
          font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace;
          color: #a9b1d6;
          height: 580px;
          border-radius: 6px;
          border: 1px solid #414868;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }}
        .window-header {{
          background: #1f2335;
          padding: 8px 15px;
          display: flex;
          align-items: center;
          border-bottom: 1px solid #414868;
        }}
        .buttons {{ display: flex; gap: 6px; width: 60px; }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .red {{ background: #f7768e; }}
        .yellow {{ background: #e0af68; }}
        .green {{ background: #9ece6a; }}
        .window-title {{ font-size: 11px; color: #565f89; flex-grow: 1; text-align: center; }}
        
        .content {{ padding: 15px; font-size: 12px; line-height: 1.6; }}
        .dir {{ color: #7aa2f7; font-weight: bold; }}
        .tree-line {{ color: #565f89; white-space: pre; }}
        .item {{ display: inline-flex; align-items: center; gap: 6px; transform: translateY(2px); }}
        .icon {{ width: 14px; height: 14px; }}
        .file {{ color: #c0caf5; }}
        .command {{ color: #9ece6a; }}
        .prompt {{ color: #bb9af7; }}
      </style>
      <div class="container">
        <div class="window-header">
          <div class="buttons">
            <div class="dot red"></div>
            <div class="dot yellow"></div>
            <div class="dot green"></div>
          </div>
          <div class="window-title">bash -- skills</div>
          <div style="width: 60px;"></div>
        </div>
        <div class="content">
          <div><span class="prompt">aldrin@frtzhahn</span>:<span class="dir">~/skills</span>$ <span class="command">tree</span></div>
          <div class="dir">.</div>
{lines_html}
        </div>
      </div>
    </div>
  </foreignObject>
</svg>"""

with open('skills.svg', 'w') as f:
    f.write(svg_template)
print("skills.svg generated.")
