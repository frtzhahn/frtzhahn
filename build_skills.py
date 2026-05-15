import urllib.request
import base64

icons_list = {
    'Arch WSL':   ('https://cdn.simpleicons.org/archlinux/1793d1', '#1793d1'),
    'CachyOS':    ('https://cdn.simpleicons.org/archlinux/13e098', '#13e098'),
    'Windows 10': ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/windows8/windows8-original.svg', '#0078d6'),
    'Android':    ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/android/android-original.svg', '#3DDC84'),
    'Kali Linux': ('https://cdn.simpleicons.org/kalilinux/557C94', '#557C94'),
    'KDE':        ('https://cdn.simpleicons.org/kde/1D99F3', '#1D99F3'),
    'GNOME':      ('https://cdn.simpleicons.org/gnome/4A86CF', '#4A86CF'),
    'Sway':       ('https://cdn.simpleicons.org/sway/333333', '#333333'),
    'i3':         ('https://cdn.simpleicons.org/i3/4C7899', '#4C7899'),
    'GlazeWM':    ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/windows8/windows8-original.svg', '#ffffff'),
    'VSCode':     ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/vscode/vscode-original.svg', '#007ACC'),
    'Vim':        ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/vim/vim-original.svg', '#019733'),
    'Neovim':     ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/neovim/neovim-original.svg', '#57A143'),
    'IDEA':       ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/intellij/intellij-original.svg', '#000000'),
    'Arduino':    ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/arduino/arduino-original.svg', '#00979D'),
    'Obsidian':   ('https://cdn.simpleicons.org/obsidian/483699', '#483699'),
    'C':          ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/c/c-original.svg', '#A8B9CC'),
    'CSS':        ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/css3/css3-original.svg', '#1572B6'),
    'HTML5':      ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/html5/html5-original.svg', '#E34F26'),
    'JavaScript': ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/javascript/javascript-original.svg', '#F7DF1E'),
    'Canva':      ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/canva/canva-original.svg', '#00C4CC'),
    'Git':        ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/git/git-original.svg', '#F05032'),
    'GitHub':     ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/github/github-original.svg', '#181717'),
    'Java':       ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/java/java-original.svg', '#007396'),
    'Figma':      ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/figma/figma-original.svg', '#F24E1E'),
    'Maven':      ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/maven/maven-original.svg', '#C71A22'),
    'JavaFX':     ('https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/java/java-original.svg', '#007396'),
}

def get_b64(url, color):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return f"data:image/svg+xml;base64,{base64.b64encode(response.read()).decode()}"
    except Exception as e:
        print(f"  Failed {url}: {e}")
        fallback = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="{color}"/></svg>'
        return f"data:image/svg+xml;base64,{base64.b64encode(fallback.encode()).decode()}"

print("Fetching icons...")
icons = {}
for name, (url, color) in icons_list.items():
    icons[name] = get_b64(url, color)

# Left column groups
left_structure = [
    ("├── ", "Operating Systems", [
        ("│   ├── ", "Arch WSL"),
        ("│   ├── ", "CachyOS"),
        ("│   ├── ", "Windows 10"),
        ("│   ├── ", "Android"),
        ("│   └── ", "Kali Linux"),
    ]),
    ("└── ", "Desktop Environments", [
        ("    ├── ", "KDE"),
        ("    ├── ", "GNOME"),
        ("    ├── ", "Sway"),
        ("    ├── ", "i3"),
        ("    └── ", "GlazeWM"),
    ]),
]

# Right column groups
right_structure = [
    ("├── ", "Editors &amp; IDEs", [
        ("│   ├── ", "VSCode"),
        ("│   ├── ", "Vim"),
        ("│   ├── ", "Neovim"),
        ("│   ├── ", "IDEA"),
        ("│   ├── ", "Arduino"),
        ("│   └── ", "Obsidian"),
    ]),
    ("└── ", "Languages &amp; Tools", [
        ("    ├── ", "C"),
        ("    ├── ", "Java"),
        ("    ├── ", "JavaScript"),
        ("    ├── ", "HTML5"),
        ("    ├── ", "CSS"),
        ("    ├── ", "Git"),
        ("    ├── ", "GitHub"),
        ("    ├── ", "Maven"),
        ("    ├── ", "JavaFX"),
        ("    ├── ", "Figma"),
        ("    └── ", "Canva"),
    ]),
]

def build_column(structure):
    html = ""
    for prefix, name, children in structure:
        html += f'<div><span class="tree-line">{prefix}</span><span class="dir">{name}</span></div>\n'
        for c_prefix, c_name in children:
            b64 = icons[c_name]
            html += (
                f'<div><span class="tree-line">{c_prefix}</span>'
                f'<span class="item"><img class="icon" src="{b64}"/> '
                f'<span class="file">{c_name}</span></span></div>\n'
            )
    return html

left_html  = build_column(left_structure)
right_html = build_column(right_structure)

# Adjusted heights for reliability
SVG_H  = 520
CONT_H = 500

svg_template = f"""<svg fill="none" viewBox="0 0 600 {SVG_H}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="100%" height="100%">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <style>
        .container {{
          background-color: #1a1b26;
          font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, monospace;
          color: #a9b1d6;
          height: {CONT_H}px;
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
          flex-shrink: 0;
        }}
        .buttons {{ display: flex; gap: 6px; width: 60px; }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .red    {{ background: #f7768e; }}
        .yellow {{ background: #e0af68; }}
        .green  {{ background: #9ece6a; }}
        .window-title {{ font-size: 11px; color: #565f89; flex-grow: 1; text-align: center; }}
        .content {{
          padding: 15px;
          font-size: 12px;
          line-height: 1.6;
          flex: 1;
        }}
        .columns-wrapper {{
          display: flex;
          width: 100%;
          margin-top: 2px;
        }}
        .column {{
          flex: 1;
        }}
        .dir       {{ color: #7aa2f7; font-weight: bold; }}
        .tree-line {{ color: #565f89; white-space: pre; }}
        .item      {{ display: inline-flex; align-items: center; gap: 6px; transform: translateY(2px); }}
        .icon      {{ width: 14px; height: 14px; }}
        .file      {{ color: #c0caf5; }}
        .command   {{ color: #9ece6a; }}
        .prompt    {{ color: #bb9af7; }}
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
          <div class="columns-wrapper">
            <div class="column">
{left_html}            </div>
            <div class="column">
{right_html}            </div>
          </div>
        </div>
      </div>
    </div>
  </foreignObject>
</svg>"""

with open('skills.svg', 'w') as f:
    f.write(svg_template)
print("skills.svg regenerated with Flexbox layout.")
