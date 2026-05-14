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

    bar_str, pct     = progress_bar(progress_ms, duration_ms)
    elapsed_fmt      = fmt_time(progress_ms)
    duration_fmt     = fmt_time(duration_ms)
    play_icon        = "▶" if is_playing else "▐▐"
    status_label     = "● NOW PLAYING" if is_playing else "◌ LAST PLAYED"
    status_color     = "#9ece6a" if is_playing else "#565f89"
    bar_fill_pct     = int(pct * 100)

    # Truncate long strings for display
    def trunc(s, n): return s if len(s) <= n else s[:n - 1] + "…"
    title_d  = trunc(title,  52)
    artist_d = trunc(artist, 52)
    album_d  = trunc(album,  52)

    svg = f"""<svg fill="none" viewBox="0 0 520 185" width="100%" xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="100%" height="100%">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ margin: 0; padding: 0; }}
        .card {{
          background: #1a1b26;
          border: 1px solid #414868;
          border-radius: 8px;
          font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', monospace;
          color: #a9b1d6;
          width: 518px;
          height: 183px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }}
        .titlebar {{
          background: #1f2335;
          border-bottom: 1px solid #414868;
          padding: 7px 14px;
          display: flex;
          align-items: center;
          gap: 6px;
          flex-shrink: 0;
        }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
        .r {{ background: #f7768e; }}
        .y {{ background: #e0af68; }}
        .g {{ background: #9ece6a; }}
        .win-title {{ flex: 1; text-align: center; font-size: 11px; color: #565f89; }}
        .body {{ padding: 14px 18px; display: flex; flex-direction: column; gap: 6px; flex: 1; }}
        .status {{ font-size: 10px; letter-spacing: 1.5px; color: {status_color}; }}
        .track  {{ font-size: 15px; font-weight: bold; color: #c0caf5; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .artist {{ font-size: 11px; color: #7aa2f7; }}
        .album  {{ font-size: 10px; color: #565f89; }}
        .prog-section {{ margin-top: 8px; }}
        .bar-wrap {{
          width: 100%;
          height: 4px;
          background: #292e42;
          border-radius: 4px;
          margin-bottom: 5px;
          position: relative;
          overflow: hidden;
        }}
        .bar-fill {{
          height: 100%;
          width: {bar_fill_pct}%;
          background: linear-gradient(90deg, #7aa2f7, #bb9af7);
          border-radius: 4px;
        }}
        .times-row {{
          display: flex;
          justify-content: space-between;
          font-size: 9px;
          color: #414868;
          margin-bottom: 6px;
        }}
        .controls-row {{
          display: flex;
          align-items: center;
          gap: 14px;
          font-size: 13px;
          color: #565f89;
        }}
        .play {{ color: #bb9af7; font-size: 14px; }}
        .vol {{ color: #414868; font-size: 10px; margin-left: auto; }}
      </style>
      <div class="card">
        <div class="titlebar">
          <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
          <span class="win-title">bash &mdash; ncmpcpp</span>
        </div>
        <div class="body">
          <div class="status">{status_label}</div>
          <div class="track">{title_d}</div>
          <div class="artist">♩ {artist_d}</div>
          <div class="album">⬡ {album_d}</div>
          <div class="prog-section">
            <div class="bar-wrap"><div class="bar-fill"></div></div>
            <div class="times-row"><span>{elapsed_fmt}</span><span>{duration_fmt}</span></div>
            <div class="controls-row">
              <span>⏮</span>
              <span class="play">{play_icon}</span>
              <span>⏭</span>
              <span>⇌</span>
              <span class="vol">vol: ████████░░ 80%</span>
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
