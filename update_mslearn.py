import os
import re
import requests

SHARE_ID = os.environ.get("MS_LEARN_SHARE_ID", "").strip()
USERNAME = "OverseerLord-8836"
TRANSCRIPT_API = f"https://learn.microsoft.com/api/profiles/transcript/share/{SHARE_ID}?locale=en-us"

def fetch_transcript_data():
    if not SHARE_ID or len(SHARE_ID) < 6:
        print("Valid MS_LEARN_SHARE_ID transcript token not provided.")
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

    try:
        res = requests.get(TRANSCRIPT_API, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json()
        print(f"Transcript API returned status {res.status_code}")
    except requests.RequestException as e:
        print(f"Transcript request failed: {e}")
    return None

def build_detailed_markdown(data):
    lines = []

    # 1. Headline Statistics
    badges_count = data.get("badgesCount", 359)
    trophies_count = data.get("trophiesCount", 81)
    reputation = data.get("reputationPoints", 468550)

    lines.append("### 📊 Microsoft Learn Summary")
    lines.append(f"- 🏆 **Trophies:** {trophies_count}")
    lines.append(f"- 🏅 **Badges & Modules Completed:** {badges_count}")
    lines.append(f"- ⚡ **Total XP / Points:** {reputation:,} XP")
    lines.append("")

    # 2. Certifications & Applied Skills
    certs = data.get("certifications", [])
    if certs:
        lines.append("### 📜 Certifications & Applied Skills")
        for c in certs:
            title = c.get("title") or c.get("name", "Certification")
            date = c.get("issuedDate", "").split("T")[0]
            url = c.get("url") or c.get("certificationUrl")
            item = f"- **[{title}]({url})**" if url else f"- **{title}**"
            if date:
                item += f" `(Issued: {date})`"
            lines.append(item)
        lines.append("")

    # 3. Learning Paths Completed
    paths = data.get("learningPaths", [])
    if paths:
        lines.append("### 🚀 Completed Learning Paths")
        lines.append("| Learning Path | Modules | Completed Date |")
        lines.append("| :--- | :---: | :---: |")
        for p in paths[:8]:
            title = p.get("title", "Learning Path")
            url = p.get("url")
            date = p.get("completedOn", "").split("T")[0]
            count = p.get("modulesCount", "-")
            link = f"[{title}]({url})" if url else title
            lines.append(f"| {link} | {count} | {date} |")
        lines.append("")

    # 4. Recent Completed Modules & Badges (Detailed Table)
    modules = data.get("modules", [])
    if modules:
        lines.append("### 🏅 Recently Completed Modules & Badges")
        lines.append("| Badge | Module Name | Completed On |")
        lines.append("| :---: | :--- | :---: |")
        for m in modules[:12]:
            title = m.get("title", "Module")
            url = m.get("url")
            date = m.get("completedOn", "").split("T")[0]
            icon = m.get("iconUrl")

            badge_img = f'<img src="{icon}" width="36" />' if icon else "🏅"
            name = f"[{title}]({url})" if url else title
            lines.append(f"| {badge_img} | {name} | {date} |")
        
        if len(modules) > 12:
            lines.append(f"\n*...and {len(modules) - 12} more modules verified on transcript.*")
        lines.append("")

    lines.append("*(Updated automatically via GitHub Actions)*")
    return "\n".join(lines)

def update_readme(content):
    readme_path = "README.md"
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r"<!-- START_SECTION:mslearn -->.*?<!-- END_SECTION:mslearn -->"
    replacement = f"<!-- START_SECTION:mslearn -->\n{content}\n<!-- END_SECTION:mslearn -->"

    if re.search(pattern, readme, re.DOTALL):
        updated = re.sub(pattern, replacement, readme, flags=re.DOTALL)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated)
        print("README updated successfully.")

if __name__ == "__main__":
    data = fetch_transcript_data()
    if data:
        md = build_detailed_markdown(data)
        update_readme(md)
    else:
        print("Could not fetch transcript details. Check MS_LEARN_SHARE_ID.")
