import urllib.request
import base64

slugs = {
    'Arch Linux': ('archlinux', '#1793d1'),
    'CachyOS': ('cachyos', '#13e098'),
    'Windows 10': ('windows', '#0078d6'),
    'Android': ('android', '#3DDC84'),
    'Kali Linux': ('kalilinux', '#557C94'),
    'KDE Plasma': ('kde', '#1D99F3'),
    'GNOME': ('gnome', '#4A86CF'),
    'Sway': ('sway', '#333333'), # might not exist
    'i3wm': ('i3', '#4C7899'), # might not exist
    'GlazeWM': ('windows', '#ffffff'), # fallback
    'VSCode': ('visualstudiocode', '#007ACC'),
    'Vim': ('vim', '#019733'),
    'Neovim': ('neovim', '#57A143'),
    'IntelliJ': ('intellijidea', '#000000'),
    'Obsidian': ('obsidian', '#483699'),
    'C': ('c', '#A8B9CC'),
    'CSS3': ('css3', '#1572B6'),
    'HTML5': ('html5', '#E34F26'),
    'JavaScript': ('javascript', '#F7DF1E'),
    'Canva': ('canva', '#00C4CC'),
    'Git': ('git', '#F05032'),
    'Arduino': ('arduino', '#00979D'),
    'Java': ('java', '#007396'), # simpleicons doesn't have java officially, might fail
    'Figma': ('figma', '#F24E1E'),
    'Maven': ('apachemaven', '#C71A22'),
    'JavaFX': ('java', '#007396'),
}

def get_b64(slug, color):
    # Try simpleicons first
    url = f"https://cdn.simpleicons.org/{slug}/{color[1:]}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            svg_data = response.read()
            return f"data:image/svg+xml;base64,{base64.b64encode(svg_data).decode()}"
    except Exception as e:
        print(f"Failed to fetch {slug}: {e}")
        # Return an empty base64 or a default generic circle/dot
        fallback = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="{color}"/></svg>'
        return f"data:image/svg+xml;base64,{base64.b64encode(fallback.encode()).decode()}"

b64_cache = {}
for name, (slug, color) in slugs.items():
    print(f"Fetching {name}...")
    b64_cache[name] = get_b64(slug, color)

print("Fetched all icons.")
