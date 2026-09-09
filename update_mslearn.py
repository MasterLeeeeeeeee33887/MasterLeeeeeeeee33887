import os
import re
import sys
import requests

USER_OR_SHARE_ID = os.environ.get("MS_LEARN_SHARE_ID", "OverseerLord-8836").strip()

def fetch_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    # Attempt 1: Fetch via Public Profile / Achievement API
    user_url = f"https://learn.microsoft.com/api/profiles/{USER_OR_SHARE_ID}"
    try:
        res = requests.get(user_url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json()
    except requests.RequestException:
        pass

    # Attempt 2: Fetch via Shared Transcript API
    transcript_url = f"https://learn.microsoft.com/api/profiles/transcript/share/{USER_OR_SHARE_ID}?locale=en-us"
    try:
        res = requests.get(transcript_url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json()
    except requests.RequestException:
        pass

    print(f"Error: Could not retrieve data for identifier '{USER_OR_SHARE_ID}'.")
    return None

def build_resume_markdown(data):
    # Extract metrics across varying Microsoft Learn API response structures
    badges_count = (
        data.get("badgesCount")
        or data.get("badgesAchievedCount")
        or data.get("badgeCount")
        or 0
    )
    trophies_count = (
        data.get("trophiesCount")
        or data.get("trophiesAchievedCount")
        or data.get("trophyCount")
        or 0
    )
    points = (
        data.get("points")
        or data.get("reputationPoints")
        or data.get("totalPoints")
        or 0
    )
    level = data.get("level", {}).get("levelNumber") if isinstance(data.get("level"), dict) else data.get("level")

    certifications = data.get("certifications", [])
    learning_paths = data.get("learningPaths", [])
    modules = data.get("modules", [])

    lines = []
    lines.append("### 📊 Microsoft Learn Stats")
    lines.append(f"- 🏆 **Trophies:** {trophies_count}")
    lines.append(f"- 🏅 **Badges:** {badges_count}")
    if level:
        lines.append(f"- 🎖️ **Level:** Level {level}")
    if points:
        lines.append(f"- ⚡ **XP Points:** {points:,}")
    lines.append("")

    if certifications:
        lines.append("### 📜 Certifications & Applied Skills")
        for cert in certifications:
            title = cert.get("title") or cert.get("name", "Certification")
            issued = cert.get("issuedDate", "").split("T")[0]
            url = cert.get("url") or cert.get("certificationUrl")
            item = f"- **[{title}]({url})**" if url else f"- **{title}**"
            if issued:
                item += f" *(Issued: {issued})*"
            lines.append(item)
        lines.append("")

    if learning_paths:
        lines.append("### 🚀 Completed Learning Paths")
        for path in learning_paths[:10]:
            title = path.get("title", "Learning Path")
            url = path.get("url")
            lines.append(f"- [{title}]({url})" if url else f"- {title}")
        lines.append("")

    if modules:
        lines.append("### 📚 Recent Completed Modules & Courses")
        for mod in modules[:10]:
            title = mod.get("title", "Module")
            url = mod.get("url")
            date = mod.get("completedOn", "").split("T")[0]
            item = f"- [{title}]({url})" if url else f"- {title}"
            if date:
                item += f" `({date})`"
            lines.append(item)
        if len(modules) > 10:
            lines.append(f"\n*...and {len(modules) - 10} more completed modules.*")
        lines.append("")

    lines.append("*(Updated automatically via GitHub Actions)*")
    return "\n".join(lines)

def update_readme(markdown_content):
    readme_path = "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()

        pattern = r"(<!-- START_SECTION:mslearn -->)(.*?)(<!-- END_SECTION:mslearn -->)"
        if not re.search(pattern, readme, flags=re.DOTALL):
            print("Warning: Anchor tags not found.")
            return

        replacement = f"\\1\n\n{markdown_content}\n\n\\3"
        updated = re.sub(pattern, replacement, readme, flags=re.DOTALL)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated)
            
        print("README.md successfully updated.")
    except FileNotFoundError:
        print("README.md not found.")

if __name__ == "__main__":
    profile_data = fetch_data()
    if profile_data:
        markdown = build_resume_markdown(profile_data)
        update_readme(markdown)
    else:
        print("No data could be formatted.")
