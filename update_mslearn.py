import os
import re
import sys
import requests

SHARE_ID = os.environ.get("MS_LEARN_SHARE_ID")

if not SHARE_ID:
    print("Error: MS_LEARN_SHARE_ID environment variable is missing.")
    sys.exit(1)

API_URL = f"https://learn.microsoft.com/api/profiles/transcript/share/{SHARE_ID}?locale=en-us"

def fetch_transcript_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch transcript: {e}")
        return None

def build_resume_markdown(data):
    # Overall summary metrics
    badges_count = data.get("badgesCount", 0)
    trophies_count = data.get("trophiesCount", 0)
    reputation_points = data.get("reputationPoints", 0)

    # Collections
    certifications = data.get("certifications", [])
    learning_paths = data.get("learningPaths", [])
    modules = data.get("modules", [])

    lines = []
    
    # 1. Summary Cards
    lines.append("### 📊 Microsoft Learn Stats")
    lines.append(f"- 🏆 **Trophies:** {trophies_count}")
    lines.append(f"- 🏅 **Badges & Modules:** {badges_count}")
    if reputation_points:
        lines.append(f"- ⚡ **Reputation / XP:** {reputation_points:,}")
    lines.append("")

    # 2. Certifications & Applied Skills
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

    # 3. Learning Paths Finished
    if learning_paths:
        lines.append("### 🚀 Completed Learning Paths")
        for path in learning_paths:
            title = path.get("title", "Learning Path")
            url = path.get("url")
            item = f"- [{title}]({url})" if url else f"- {title}"
            lines.append(item)
        lines.append("")

    # 4. Recent Courses & Modules
    if modules:
        lines.append("### 📚 Recent Completed Modules & Courses")
        # Display the 10 most recent modules
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

        # Flexible pattern matching any whitespace/newlines between tags
        pattern = r"(<!-- START_SECTION:mslearn -->)(.*?)(<!-- END_SECTION:mslearn -->)"
        
        if not re.search(pattern, readme, flags=re.DOTALL):
            print("Warning: Anchor tags <!-- START_SECTION:mslearn --> not found in README.md.")
            return

        replacement = f"\\1\n\n{markdown_content}\n\n\\3"
        updated = re.sub(pattern, replacement, readme, flags=re.DOTALL)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated)
            
        print("README.md successfully updated.")
    except FileNotFoundError:
        print("README.md not found in the root directory.")

if __name__ == "__main__":
    transcript = fetch_transcript_data()
    if transcript:
        content = build_resume_markdown(transcript)
        update_readme(content)
