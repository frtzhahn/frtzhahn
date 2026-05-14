"""
build_spotify.py
Fetches the currently playing (or last played) Spotify track
and generates an ncmpcpp-styled terminal SVG card.
"""
import os
import sys
import urllib.request
import urllib.parse
import base64
import json
import math

# ── Credentials (injected by GitHub Actions) ─────────────────────────────────
CLIENT_ID     = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]

# ── Get a fresh access token ──────────────────────────────────────────────────
def get_access_token():
    creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    data  = urllib.parse.urlencode({
        "grant_type":    "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }).encode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type":  "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())["access_token"]

# ── Fetch track info ──────────────────────────────────────────────────────────
def fetch_track(token):
    headers = {"Authorization": f"Bearer {token}"}

    # Try currently playing first
    req = urllib.request.Request(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req) as res:
            if res.status == 200:
                data = json.loads(res.read())
                if data and data.get("item"):
                    return data["item"], data.get("is_playing", False), data.get("progress_ms", 0)
    except Exception:
        pass

    # Fall back to recently played
    req = urllib.request.Request(
        "https://api.spotify.com/v1/me/player/recently-played?limit=1",
        headers=headers,
    )
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
        if data.get("items"):
            return data["items"][0]["track"], False, 0

    return None, False, 0

# ── Fetch and embed album art ─────────────────────────────────────────────────
def fetch_album_art(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as res:
            data = res.read()
            return f"data:image/jpeg;base64,{base64.b64encode(data).decode()}"
    except Exception:
        return None

# ── Build progress bar (ncmpcpp style) ───────────────────────────────────────
def progress_bar(progress_ms, duration_ms, width=38):
    if duration_ms == 0:
        pct = 0.0
    else:
        pct = min(progress_ms / duration_ms, 1.0)
    filled = math.floor(pct * width)
    bar    = "─" * filled + "●" + "─" * (width - filled)
    return bar[:width], pct

def fmt_time(ms):
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"

# ── Generate SVG ─────────────────────────────────────────────────────────────
def generate_svg(track, is_playing, progress_ms):
    title       = track["name"]
    artist      = ", ".join(a["name"] for a in track["artists"])
    album       = track["album"]["name"]
    duration_ms = track["duration_ms"]
    art_url     = track["album"]["images"][0]["url"] if track["album"]["images"] else None

    art_b64     = fetch_album_art(art_url) if art_url else None
    art_img     = f'<image href="{art_b64}" x="20" y="72" width="80" height="80" rx="6"/>' if art_b64 else \
                  '<rect x="20" y="72" width="80" height="80" rx="6" fill="#1f2335" stroke="#414868" stroke-width="1"/>'

    bar_str, pct     = progress_bar(progress_ms, duration_ms)
    elapsed_fmt      = fmt_time(progress_ms)
    duration_fmt     = fmt_time(duration_ms)
    play_icon        = "▶" if is_playing else "⏸"
    status_text      = "Now Playing" if is_playing else "Last Played"
    bar_fill_width   = int(pct * 336)  # max bar pixel width

    # Truncate long strings
    def trunc(s, n): return s if len(s) <= n else s[:n-1] + "…"
    title_disp  = trunc(title,  42)
    artist_disp = trunc(artist, 42)
    album_disp  = trunc(album,  42)

    svg = f"""<svg fill="none" viewBox="0 0 500 210" width="100%" xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="100%" height="100%">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        .card {{
          background: #1a1b26;
          border: 1px solid #414868;
          border-radius: 8px;
          font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace;
          color: #a9b1d6;
          width: 498px;
          height: 208px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }}
        .titlebar {{
          background: #1f2335;
          border-bottom: 1px solid #414868;
          padding: 6px 14px;
          display: flex;
          align-items: center;
          gap: 6px;
        }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .r {{ background: #f7768e; }}
        .y {{ background: #e0af68; }}
        .g {{ background: #9ece6a; }}
        .win-title {{ flex: 1; text-align: center; font-size: 11px; color: #565f89; }}
        .body {{
          display: flex;
          flex-direction: row;
          flex: 1;
          padding: 12px 16px 12px 12px;
          gap: 16px;
          align-items: flex-start;
        }}
        .art {{
          width: 80px;
          height: 80px;
          border-radius: 6px;
          border: 1px solid #414868;
          flex-shrink: 0;
          overflow: hidden;
          background: #1f2335;
        }}
        .art img {{ width: 80px; height: 80px; border-radius: 6px; object-fit: cover; }}
        .info {{
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 3px;
          padding-top: 2px;
        }}
        .status {{ font-size: 10px; color: #1abc9c; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }}
        .track  {{ font-size: 14px; color: #c0caf5; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .artist {{ font-size: 11px; color: #7aa2f7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .album  {{ font-size: 10px; color: #565f89; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .controls {{
          margin-top: 10px;
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 12px;
          color: #565f89;
        }}
        .play-btn {{ font-size: 16px; color: #bb9af7; }}
        .progress-wrap {{ flex: 1; display: flex; flex-direction: column; gap: 3px; }}
        .bar-track {{ height: 3px; background: #292e42; border-radius: 2px; position: relative; }}
        .bar-fill  {{ height: 3px; background: linear-gradient(90deg, #7aa2f7, #bb9af7); border-radius: 2px; width: {bar_fill_width}px; max-width: 336px; }}
        .times {{ display: flex; justify-content: space-between; font-size: 9px; color: #414868; }}
        .prompt {{ font-size: 10px; color: #565f89; margin-top: 8px; }}
        .prompt .cmd {{ color: #9ece6a; }}
        .prompt .arg {{ color: #e0af68; }}
      </style>
      <div class="card">
        <div class="titlebar">
          <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
          <span class="win-title">bash &mdash; ncmpcpp</span>
        </div>
        <div class="body">
          <div class="art">{"<img src='" + art_b64 + "'/>" if art_b64 else ""}</div>
          <div class="info">
            <div class="status">◉ {status_text}</div>
            <div class="track">{title_disp}</div>
            <div class="artist">♩ {artist_disp}</div>
            <div class="album">⬡ {album_disp}</div>
            <div class="controls">
              <span>⏮</span>
              <span class="play-btn">{play_icon}</span>
              <span>⏭</span>
              <div class="progress-wrap">
                <div class="bar-track"><div class="bar-fill"></div></div>
                <div class="times"><span>{elapsed_fmt}</span><span>{duration_fmt}</span></div>
              </div>
            </div>
            <div class="prompt">
              <span class="cmd">ncmpcpp</span> <span class="arg">--host</span> spotify.local
            </div>
          </div>
        </div>
      </div>
    </div>
  </foreignObject>
</svg>"""
    return svg

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching Spotify token...")
    token = get_access_token()

    print("Fetching track info...")
    track, is_playing, progress_ms = fetch_track(token)

    if not track:
        print("No track data available. Writing placeholder SVG.")
        svg = generate_svg({
            "name": "Not listening right now",
            "artists": [{"name": "—"}],
            "album": {"name": "—", "images": []},
            "duration_ms": 0,
        }, False, 0)
    else:
        print(f"Track: {track['name']} – {', '.join(a['name'] for a in track['artists'])}")
        svg = generate_svg(track, is_playing, progress_ms)

    with open("spotify.svg", "w") as f:
        f.write(svg)

    print("spotify.svg generated.")
