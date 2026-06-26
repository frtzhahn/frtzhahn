import re

def main():
    # Read files
    with open('header.svg', 'r') as f:
        header_content = f.read()
    with open('wakatime.svg', 'r') as f:
        waka_content = f.read()
    with open('skills.svg', 'r') as f:
        skills_content = f.read()

    # 1. Extract base64 image string from header.svg
    img_match = re.search(r'<img[^>]*src="([^"]+)"', header_content)
    if not img_match:
        raise ValueError("Could not find base64 image in header.svg")
    base64_img = img_match.group(1)

    # 2. Extract WakaTime stats content
    start_waka = waka_content.find('<div class="section">')
    if start_waka == -1:
        raise ValueError("Could not find section div in wakatime.svg")
    
    end_waka = waka_content.rfind('</foreignObject>')
    if end_waka == -1:
        raise ValueError("Could not find </foreignObject> in wakatime.svg")
    for _ in range(3):
        end_waka = waka_content.rfind('</div>', 0, end_waka)
    
    waka_html = waka_content[start_waka:end_waka].strip()
    
    # Namespace WakaTime classes to prevent collision with header progress bars
    waka_html = waka_html.replace('class="bar-row"', 'class="waka-bar-row"')
    waka_html = waka_html.replace('class="bar-name"', 'class="waka-bar-name"')
    waka_html = waka_html.replace('class="bar-bg"', 'class="waka-bar-bg"')
    waka_html = waka_html.replace('class="bar-fill"', 'class="waka-bar-fill"')
    waka_html = waka_html.replace('class="bar-val"', 'class="waka-bar-val"')

    # 3. Parse Skills content into a 2x2 grid layout
    start_skills = skills_content.find('<div class="columns-wrapper">')
    if start_skills == -1:
        raise ValueError("Could not find columns-wrapper in skills.svg")
        
    end_skills = skills_content.rfind('</foreignObject>')
    if end_skills == -1:
         raise ValueError("Could not find </foreignObject> in skills.svg")
    for _ in range(5):
         end_skills = skills_content.rfind('</div>', 0, end_skills)
         
    skills_lines = skills_content[start_skills:end_skills].split('\n')
    
    categories = []
    current_category = None
    
    for line in skills_lines:
        cat_match = re.search(r'<span class="dir">([^<]+)</span>', line)
        if cat_match:
            cat_name = cat_match.group(1).strip()
            # If the category is Languages & Tools, rename to LANGUAGES/TOOLS
            if "languages" in cat_name.lower():
                cat_name = "LANGUAGES/TOOLS"
            else:
                cat_name = cat_name.upper().replace('&AMP;', '&amp;')
            current_category = {"name": cat_name, "items": []}
            categories.append(current_category)
            continue
            
        item_match = re.search(r'<img class="icon" src="([^"]+)"/>\s*<span class="file">([^<]+)</span>', line)
        if item_match and current_category is not None:
            img_src = item_match.group(1).strip()
            item_name = item_match.group(2).strip()
            current_category["items"].append({"name": item_name, "icon": img_src})
            
    # Format categories into a 2-column stacked layout
    col1_html = ""
    col2_html = ""
    
    for col_idx, cat_indices in enumerate([[0, 2], [1, 3]]):
        col_html = ""
        for idx in cat_indices:
            if idx < len(categories):
                cat = categories[idx]
                cat_html = '              <div class="skills-category">\n'
                cat_html += f'                <div class="skills-category-title">{cat["name"]}</div>\n'
                cat_html += '                <div class="skills-category-items">\n'
                for item in cat["items"]:
                    item_name_xml = item["name"].replace('&', '&amp;')
                    cat_html += '                  <div class="skill-entry">\n'
                    cat_html += f'                    <img class="skill-icon" src="{item["icon"]}" />\n'
                    cat_html += f'                    <span class="skill-name-type">{item_name_xml}</span>\n'
                    cat_html += '                  </div>\n'
                cat_html += '                </div>\n'
                cat_html += '              </div>\n'
                
                # Spacing between categories in the same column
                if idx == cat_indices[0]:
                    cat_html += '              <div style="height: 16px;"></div>\n'
                col_html += cat_html
        if col_idx == 0:
            col1_html = col_html
        else:
            col2_html = col_html
            
    skills_grid_html = f"""<div class="skills-grid">
            <div class="skills-column">
{col1_html}            </div>
            <div class="skills-column">
{col2_html}            </div>
          </div>"""

    # Consolidated styles
    styles = """        .container {
          box-sizing: border-box;
          width: calc(100% - 2px);
          background-color: #1a1b26;
          font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'DejaVu Sans Mono', monospace;
          color: #a9b1d6;
          height: 1448px; /* Increased from 1200px to accommodate full grid without scrolling */
          border-radius: 6px;
          overflow: hidden;
          border: 1px solid #414868;
          margin: 1px;
          display: flex;
          flex-direction: column;
        }
        .window-header {
          background: #1f2335;
          padding: 8px 15px;
          display: flex;
          align-items: center;
          border-bottom: 1px solid #414868;
          flex-shrink: 0;
        }
        .buttons { display: flex; gap: 6px; width: 60px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; }
        .red { background: #f7768e; }
        .yellow { background: #e0af68; }
        .green { background: #9ece6a; }
        .window-title { font-size: 11px; color: #565f89; flex-grow: 1; text-align: center; }
        .header-spacer { width: 60px; }

        .content { 
          padding: 20px 15px; 
          display: flex; 
          flex-direction: column; 
          flex-grow: 1;
        }
        
        .section-spacer {
          height: 24px;
          flex-shrink: 0;
        }

        /* Unified Prompt Prefix and Command Styling */
        .prompt-line {
          font-size: 14px;
          margin-bottom: 8px;
          flex-shrink: 0;
        }
        .prompt { color: #bb9af7; }
        .dir    { color: #7aa2f7; font-weight: bold; }
        .accent { color: #bb9af7; }

        .cmd-wrap {
          display: inline-block;
          vertical-align: bottom;
          white-space: nowrap;
          overflow: hidden;
          width: 0;
          color: #7aa2f7;
        }
        .cmd-cursor {
          display: inline-block;
          width: 7px;
          height: 14px;
          background-color: #7aa2f7;
          vertical-align: middle;
          margin-left: 4px;
          animation: cursor-blink-sync 0.8s infinite;
        }
        @keyframes cursor-blink-sync {
          0%, 49% { opacity: 1; }
          50%, 100% { opacity: 0; }
        }

        /* Typing Animations for Commands */
        .cmd-fastfetch { animation: type-fastfetch 20s infinite; }
        .cmd-cat       { animation: type-cat 20s infinite; }
        .cmd-htop      { animation: type-htop 20s infinite; }
        .cmd-skills    { animation: type-skills 20s infinite; }

        @keyframes type-fastfetch {
          0% { width: 0; }
          5% { width: 0; animation-timing-function: steps(9, end); }
          15% { width: 9ch; }
          85% { width: 9ch; animation-timing-function: steps(9, end); }
          95% { width: 0; }
          100% { width: 0; }
        }
        @keyframes type-cat {
          0% { width: 0; }
          5% { width: 0; animation-timing-function: steps(16, end); }
          15% { width: 16ch; }
          85% { width: 16ch; animation-timing-function: steps(16, end); }
          95% { width: 0; }
          100% { width: 0; }
        }
        @keyframes type-htop {
          0% { width: 0; }
          5% { width: 0; animation-timing-function: steps(12, end); }
          15% { width: 12ch; }
          85% { width: 12ch; animation-timing-function: steps(12, end); }
          95% { width: 0; }
          100% { width: 0; }
        }
        @keyframes type-skills {
          0% { width: 0; }
          5% { width: 0; animation-timing-function: steps(16, end); }
          15% { width: 16ch; }
          85% { width: 16ch; animation-timing-function: steps(16, end); }
          95% { width: 0; }
          100% { width: 0; }
        }

        /* Output Fades - Unified 5s staggered transition pacing */
        .fastfetch-output, .aboutme-output, .waka-output, .skills-grid {
          animation: output-fade 20s infinite;
        }
        @keyframes output-fade {
          0%, 15% { opacity: 0; }
          40%, 65% { opacity: 1; }
          90%, 100% { opacity: 0; }
        }
        
        /* Fastfetch Logo and Columns */
        .fastfetch { display: flex; flex-direction: row; gap: 20px; align-items: center; padding: 0px; flex-shrink: 0; }
        .ascii-art { color: #a9b1d6; font-size: 14px; line-height: 1.2; font-weight: bold; white-space: pre; }
        .sys-info { flex: 1; display: flex; flex-direction: column; gap: 4px; font-size: 11px; flex-shrink: 0; }
        
        /* Progress Bar Styling (Fastfetch and WakaTime) - 5s Fill Rate */
        .bar-container { display: flex; align-items: center; gap: 10px; }
        .bar-bg { background: #24283b; height: 6px; border-radius: 3px; flex: 1; }
        .bar-fill, .waka-bar-fill { 
          height: 100%; border-radius: 3px; 
          transform-origin: left;
          animation: fill-bar 20s infinite;
        }
        @keyframes fill-bar {
          0%, 15% { transform: scaleX(0); }
          40%, 65% { transform: scaleX(1); }
          90%, 100% { transform: scaleX(0); }
        }

        .OS {
          color: #a9b1d6; 
          line-height: 1.4;
          padding: 0px 5px;
        }
        .footer-logs {
          padding: 10px 15px;
          font-size: 10px;
          color: #414868;
          display: flex;
          justify-content: space-between;
          border-top: 1px solid #24283b;
          margin-top: auto;
        }
      
        /* Bio Section Sequential Typing and Course/Traits Typography - Legible Deletion Rate */
        .line {
          overflow: hidden;
          white-space: nowrap;
          width: 0;
          display: block;
        }
        .line-1 { animation: type-bio-1 20s infinite; }
        .line-2 { animation: type-bio-2 20s infinite; }
        .line-3 { animation: type-bio-3 20s infinite; }
        @keyframes type-bio-1 {
          0%, 10% { width: 0; }
          10% { width: 0; animation-timing-function: steps(35, end); }
          18%, 60% { width: 35ch; }
          85%, 100% { width: 0; }
        }
        @keyframes type-bio-2 {
          0%, 18% { width: 0; }
          18% { width: 0; animation-timing-function: steps(40, end); }
          26%, 60% { width: 40ch; }
          85%, 100% { width: 0; }
        }
        @keyframes type-bio-3 {
          0%, 26% { width: 0; }
          26% { width: 0; animation-timing-function: steps(34, end); }
          34%, 60% { width: 34ch; }
          85%, 100% { width: 0; }
        }

        .info-line {
          overflow: hidden;
          white-space: nowrap;
          max-width: 0;
          width: max-content;
          border-right: 2px solid transparent;
          animation: type-info 20s infinite;
        }
        @keyframes type-info {
          0%, 10% { max-width: 0; border-right-color: transparent; }
          11% { border-right-color: #bb9af7; }
          35%, 60% { max-width: 50ch; border-right-color: transparent; }
          61% { border-right-color: #bb9af7; }
          85%, 100% { max-width: 0; border-right-color: transparent; }
        }
        .info-line:nth-child(1) { animation-delay: 0.2s; }
        .info-line:nth-child(2) { animation-delay: 0.6s; }

        /* WakaTime Stats Styling */
        .section { flex-shrink: 0; }
        .section-label { 
          color: #565f89; font-size: 15px; text-transform: uppercase; margin-bottom: 8px; font-weight: bold; 
          display: block; border-bottom: 1px solid #24283b; padding-bottom: 2px;
          overflow: hidden; white-space: nowrap; max-width: 0; width: max-content;
          border-right: 2px solid transparent;
          animation: type-section 20s infinite;
        }
        @keyframes type-section {
          0%, 10% { max-width: 0; border-right-color: transparent; }
          11% { border-right-color: #bb9af7; }
          35%, 60% { max-width: 25ch; border-right-color: transparent; }
          61% { border-right-color: #bb9af7; }
          85%, 100% { max-width: 0; border-right-color: transparent; }
        }
        
        .waka-bar-row { 
          display: flex; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 11px; 
          opacity: 0;
          animation: fade-row 20s infinite forwards;
        }
        @keyframes fade-row {
          0%, 10% { opacity: 0; transform: translateX(-10px); }
          35%, 60% { opacity: 1; transform: translateX(0); }
          85%, 100% { opacity: 0; transform: translateX(10px); }
        }
        .waka-bar-row:nth-child(1) { animation-delay: 0.1s; }
        .waka-bar-row:nth-child(2) { animation-delay: 0.3s; }
        .waka-bar-row:nth-child(3) { animation-delay: 0.5s; }
        .waka-bar-row:nth-child(4) { animation-delay: 0.7s; }
        .waka-bar-row:nth-child(5) { animation-delay: 0.9s; }
        .waka-bar-row:nth-child(6) { animation-delay: 1.1s; }
        .waka-bar-row:nth-child(7) { animation-delay: 1.3s; }
        .waka-bar-row:nth-child(8) { animation-delay: 1.5s; }
        .waka-bar-row:nth-child(n+9) { animation-delay: 1.7s; }

        .waka-bar-name { min-width: 70px; color: #7aa2f7; }
        .waka-bar-bg { flex-grow: 1; background: #24283b; height: 8px; border-radius: 4px; overflow: hidden; }
        .waka-bar-val { min-width: 35px; text-align: right; color: #a9b1d6; }

        .list-container { display: flex; flex-direction: column; gap: 12px; flex-shrink: 0; }
        .stat-group { display: flex; flex-direction: column; gap: 4px; }
        .stat-item { 
          color: #a9b1d6; font-size: 12px; padding-left: 10px; border-left: 2px solid #24283b; 
          overflow: hidden; white-space: nowrap; max-width: 0; width: max-content;
          border-right: 2px solid transparent;
          animation: type-stat 20s infinite forwards;
        }
        @keyframes type-stat {
          0%, 10% { max-width: 0; border-right-color: transparent; }
          11% { border-right-color: #7aa2f7; }
          35%, 60% { max-width: 30ch; border-right-color: transparent; }
          61% { border-right-color: #7aa2f7; }
          85%, 100% { max-width: 0; border-right-color: transparent; }
        }
        .stat-item:nth-child(1) { animation-delay: 0.1s; }
        .stat-item:nth-child(2) { animation-delay: 0.5s; }
        .stat-item:nth-child(3) { animation-delay: 0.9s; }
        .stat-item:nth-child(4) { animation-delay: 1.3s; }
        .stat-item:nth-child(5) { animation-delay: 1.7s; }
        .stat-item:nth-child(6) { animation-delay: 2.1s; }
        .stat-item:nth-child(7) { animation-delay: 2.5s; }
        .stat-item:nth-child(8) { animation-delay: 2.9s; }
        .stat-item:nth-child(n+9) { animation-delay: 3.3s; }
        
        .cyan { color: #73daca; }
        .green-text { color: #9ece6a; }
        .blue { color: #7aa2f7; }

        /* Skills 2x2 Grid Layout */
        .skills-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          margin-top: 8px;
        }
        .skills-column {
          display: flex;
          flex-direction: column;
        }
        .skills-category {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .skills-category-title {
          color: #7aa2f7;
          font-size: 12px;
          font-weight: bold;
          text-transform: uppercase;
          margin-bottom: 6px;
          border-bottom: 1px solid #24283b;
          padding-bottom: 2px;
          overflow: hidden;
          white-space: nowrap;
          max-width: 0;
          width: max-content;
          border-right: 2px solid transparent;
          animation: type-section 20s infinite;
        }
        /* Stagger category headers */
        .skills-column:nth-child(1) .skills-category:nth-child(1) .skills-category-title { animation-delay: 0s; }
        .skills-column:nth-child(2) .skills-category:nth-child(1) .skills-category-title { animation-delay: 0.2s; }
        .skills-column:nth-child(1) .skills-category:nth-child(3) .skills-category-title { animation-delay: 0.4s; }
        .skills-column:nth-child(2) .skills-category:nth-child(3) .skills-category-title { animation-delay: 0.6s; }

        .skills-category-items {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .skill-entry {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          color: #c0caf5;
        }
        .skill-icon {
          width: 14px;
          height: 14px;
          vertical-align: middle;
        }
        .skill-name-type {
          display: inline-block;
          vertical-align: bottom;
          overflow: hidden;
          white-space: nowrap;
          max-width: 0;
          width: max-content;
          border-right: 2px solid transparent;
          animation: type-stat 20s infinite forwards;
        }
        /* Stagger grid list items */
        .skill-entry:nth-child(1) .skill-name-type { animation-delay: 0.1s; }
        .skill-entry:nth-child(2) .skill-name-type { animation-delay: 0.3s; }
        .skill-entry:nth-child(3) .skill-name-type { animation-delay: 0.5s; }
        .skill-entry:nth-child(4) .skill-name-type { animation-delay: 0.7s; }
        .skill-entry:nth-child(5) .skill-name-type { animation-delay: 0.9s; }
        .skill-entry:nth-child(6) .skill-name-type { animation-delay: 1.1s; }
        .skill-entry:nth-child(7) .skill-name-type { animation-delay: 1.3s; }
        .skill-entry:nth-child(8) .skill-name-type { animation-delay: 1.5s; }
        .skill-entry:nth-child(9) .skill-name-type { animation-delay: 1.7s; }
        .skill-entry:nth-child(10) .skill-name-type { animation-delay: 1.9s; }
        .skill-entry:nth-child(n+11) .skill-name-type { animation-delay: 2.1s; }

        /* Global final prompt cursor */
        .terminal-cursor {
          border-right: 2px solid #7aa2f7;
          animation: terminal-cursor-blink 0.7s infinite;
        }
        @keyframes terminal-cursor-blink { 50% { border-color: transparent } }
"""

    # Assemble the final SVG (regular string, no 'f' prefix)
    svg_template = """<svg fill="none" viewBox="0 0 600 1450" width="600" height="1450" xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="600" height="1450">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <style>
{styles}      </style>
      <div class="container">
        <div class="window-header">
          <div class="buttons">
            <div class="dot red"></div>
            <div class="dot yellow"></div>
            <div class="dot green"></div>
          </div>
          <div class="window-title">aldrin@frtzhahn: ~</div>
          <div class="header-spacer"></div>
        </div>

        <div class="content">
          <!-- 1. Header and Bio Section -->
          <div class="fastfetch-block" style="display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; padding: 0 10px;">
            <div class="prompt-line">
              <span class="prompt">aldrin@frtzhahn</span>:<span class="dir">~</span>$ <span class="cmd-wrap cmd-fastfetch">fastfetch</span><span class="cmd-cursor"></span>
            </div>
            
            <div class="fastfetch-output">
              <div class="fastfetch">
                <div class="ascii-art" style="display:flex; align-items:center; justify-content:center;">
                  <img src="{base64_img}" width="120" />
                </div>
                
                <div class="sys-info">
                  <div class="bar-container">
                    <span style="width: 80px; color: #7aa2f7;">will_to_code</span>
                    <div class="bar-bg"><div class="bar-fill" style="width: 50%; background: #bb9af7;"></div></div>
                    <span style="width: 25px; text-align: right;">50%</span>
                  </div>
                  <div class="bar-container">
                    <span style="width: 80px; color: #bb9af7;">irl_age</span>
                    <div class="bar-bg"><div class="bar-fill" style="width: 18%; background: #bb9af7;"></div></div>
                    <span style="width: 25px; text-align: right;">18%</span>
                  </div>
                  <div class="bar-container">
                    <span style="width: 80px; color: #bb9af7;">college_level</span>
                    <div class="bar-bg"><div class="bar-fill" style="width: 25%; background: #f79acf;"></div></div>
                    <span style="width: 25px; text-align: right;">25%</span>
                  </div>
                  <div style="color: #414868; margin: 4px 0;">-------------------------------------------------------------</div>
                  <div class="OS" style="display: flex; flex-direction: column; gap: 4px;">
                    <div class="info-line"><span style="color: #7aa2f7; font-weight: bold;">COURSE</span>: Bachelor of Science in Computer Science</div>
                    <div class="info-line"><span style="color: #7aa2f7; font-weight: bold;">TRAITS</span>: Procrastinator, Crammer, Night Owl</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="section-spacer" style="height: 12px; flex-shrink: 0;"></div>

            <div class="prompt-line">
              <span class="prompt">aldrin@frtzhahn</span>:<span class="dir">~</span>$ <span class="cmd-wrap cmd-cat">cat about_me.txt</span><span class="cmd-cursor"></span>
            </div>
            
            <div class="aboutme-output" style="margin-top: 4px; color: #9ece6a;">
              <div class="line line-1">&gt; Hello, I'm <span class="accent">Aldrin James A. Alciso</span></div>
              <div class="line line-2">&gt; Student at <span class="accent">University of Caloocan City</span></div>
              <div class="line line-3">&gt; Exploring new things everyday :3</div>
            </div>
          </div>

          <div class="section-spacer"></div>

          <!-- 2. WakaTime Prompt and Stats Section (Wrapped for layout isolation) -->
          <div class="wakatime-block" style="display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; padding: 0 10px;">
            <div class="prompt-line">
              <span class="prompt">aldrin@frtzhahn</span>:<span class="dir">~</span>$ <span class="cmd-wrap cmd-htop">htop --stats</span><span class="cmd-cursor"></span>
            </div>
            <div class="waka-output">
{waka_html}            </div>
          </div>

          <div class="section-spacer"></div>

          <!-- 3. Skills Section (Wrapped for layout isolation) -->
          <div class="skills-block" style="display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; padding: 0 10px;">
            <div class="prompt-line">
              <span class="prompt">aldrin@frtzhahn</span>:<span class="dir">~</span>$ <span class="cmd-wrap cmd-skills">cat ~/skills.txt</span><span class="cmd-cursor"></span>
            </div>
            <div class="skills-grid-output">
{skills_grid_html}            </div>
          </div>

          <div class="section-spacer"></div>

          <!-- 4. Global final prompt cursor -->
          <div style="flex-shrink: 0; padding: 0 10px;">
            <span class="prompt">aldrin@frtzhahn</span>:<span class="dir">~</span>$ <span class="terminal-cursor">_</span>
          </div>

        </div>

        <div class="footer-logs">
          <span>LOGS: monitoring pid 1476</span>
          <span class="accent">"STATUS: EN_COURS"</span>
        </div>
      </div>
    </div>
  </foreignObject>
</svg>
"""

    # Replace formatting placeholders
    svg_template = svg_template.replace('{styles}', styles)
    svg_template = svg_template.replace('{base64_img}', base64_img)
    svg_template = svg_template.replace('{waka_html}', waka_html)
    svg_template = svg_template.replace('{skills_grid_html}', skills_grid_html)

    with open('profile.svg', 'w') as f:
        f.write(svg_template)

    print("Success: profile.svg unified template generated.")

if __name__ == '__main__':
    main()
