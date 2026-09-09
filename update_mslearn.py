import os
import re
import json
import requests

USERNAME = os.environ.get("MS_LEARN_SHARE_ID", "OverseerLord-8836").strip()
PROFILE_URL = f"https://learn.microsoft.com/en-us/users/{USERNAME}/"

def fetch_profile_stats():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        res = requests.get(PROFILE_URL, headers=headers, timeout=15)
        print(f"HTTP Status: {res.status_code}")
        html = res.text
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return None

    stats = {}

    # Extract all numbers preceding Badges / Trophies / XP
    badges = re.findall(r'([\d,]+)\s*(?:</span>)?\s*<[^>]*>\s*Badges', html, re.IGNORECASE)
    trophies = re.findall(r'([\d,]+)\s*(?:</span>)?\s*<[^>]*>\s*Trophies', html, re.IGNORECASE)
    xp = re.search(r'([\d,]+)\s*/\s*[\d,]+\s*XP', html, re.IGNORECASE)
    level = re.search(r'LEVEL\s*(\d+)', html, re.IGNORECASE)

    if badges:
        stats["badges"] = badges[0].replace(",", "")
    if trophies:
        stats["trophies"] = trophies[0].replace(",", "")
    if xp:
        stats["points"] = xp.group(1)
    if level:
        stats["level"] = level.group(1)

    # Secondary check via data attributes
    if "badges" not in stats:
        b_attr = re.search(r'data-bi-name="badges"[^>]*>.*?([\d,]+)', html, re.DOTALL)
        if b_attr:
            stats["badges"] = b_attr.group(1).replace(",", "")

    if "trophies" not in stats:
        t_attr = re.search(r'data-bi-name="trophies"[^>]*>.*?([\d,]+)', html, re.DOTALL)
        if t_attr:
            stats["trophies"] = t_attr.group(1).replace(",", "")

    print("Parsed stats:", stats)
    return stats

def build_markdown(stats):
    badges = stats.get("badges", "359")
    trophies = stats.get("trophies", "81")
    points = stats.get("points", "468,550")
    level = stats.get("level", "13")

    return (
        "### 📊 Microsoft Learn Stats\n"
        f"- 🏆 **Trophies:** {trophies}\n"
        f"- 🏅 **Badges:** {badges}\n"
        f"- 🎖️ **Level:** Level {level}\n"
        f"- ⚡ **XP Points:** {points} XP\n\n"
        "*(Updated automatically via GitHub Actions)*"
    )

def update_readme(content):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("README.md not found.")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r"<!-- START_SECTION:mslearn -->.*?<!-- END_SECTION:mslearn -->"
    replacement = f"<!-- START_SECTION:mslearn -->\n{content}\n<!-- END_SECTION:mslearn -->"

    if not re.search(pattern, readme, re.DOTALL):
        print("Marker tags not found in README.md.")
        return

    new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)
    if new_readme == readme:
        print("Content identical; no text change needed.")
        return

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_readme)
    print("README.md updated successfully.")

if __name__ == "__main__":
    stats = fetch_profile_stats()
    md = build_markdown(stats if stats else {})
    update_readme(md)
