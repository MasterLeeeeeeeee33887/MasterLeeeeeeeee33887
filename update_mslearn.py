import os
import re
import json
import requests

USERNAME = os.environ.get("MS_LEARN_SHARE_ID", "OverseerLord-8836").strip()
PROFILE_URL = f"https://learn.microsoft.com/en-us/users/{USERNAME}/"

def fetch_profile_stats():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        res = requests.get(PROFILE_URL, headers=headers, timeout=15)
        res.raise_for_status()
        html = res.text
    except requests.RequestException as e:
        print(f"Error loading profile page: {e}")
        return None

    stats = {}

    # 1. Try to find the embedded initial hydration JSON state
    json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            props = data.get("props", {}).get("pageProps", {})
            profile_data = props.get("profile", {}) or props.get("user", {})
            if profile_data:
                stats["badges"] = profile_data.get("badgesCount") or profile_data.get("badgeCount")
                stats["trophies"] = profile_data.get("trophiesCount") or profile_data.get("trophyCount")
                stats["points"] = profile_data.get("points") or profile_data.get("reputationPoints")
                stats["level"] = profile_data.get("level", {}).get("levelNumber") if isinstance(profile_data.get("level"), dict) else profile_data.get("level")
        except Exception:
            pass

    # 2. Fallback: Direct regex extraction from server-rendered HTML elements
    if not stats.get("badges"):
        b_match = re.search(r'([\d,]+)\s*(?:</span>)?\s*<[^>]+>\s*Badges', html, re.IGNORECASE) or \
                  re.search(r'data-bi-name="badges"[^>]*>.*?([\d,]+)', html, re.DOTALL)
        if b_match:
            stats["badges"] = b_match.group(1).replace(",", "")

    if not stats.get("trophies"):
        t_match = re.search(r'([\d,]+)\s*(?:</span>)?\s*<[^>]+>\s*Trophies', html, re.IGNORECASE) or \
                  re.search(r'data-bi-name="trophies"[^>]*>.*?([\d,]+)', html, re.DOTALL)
        if t_match:
            stats["trophies"] = t_match.group(1).replace(",", "")

    if not stats.get("points"):
        xp_match = re.search(r'([\d,]+)\s*/\s*[\d,]+\s*XP', html, re.IGNORECASE)
        if xp_match:
            stats["points"] = xp_match.group(1)

    if not stats.get("level"):
        lvl_match = re.search(r'LEVEL\s*(\d+)', html, re.IGNORECASE)
        if lvl_match:
            stats["level"] = lvl_match.group(1)

    return stats

def build_markdown(stats):
    badges = stats.get("badges", 0)
    trophies = stats.get("trophies", 0)
    points = stats.get("points")
    level = stats.get("level")

    lines = [
        "### 📊 Microsoft Learn Stats",
        f"- 🏆 **Trophies:** {trophies}",
        f"- 🏅 **Badges:** {badges}"
    ]

    if level:
        lines.append(f"- 🎖️ **Level:** Level {level}")
    if points:
        lines.append(f"- ⚡ **XP Points:** {points} XP" if "XP" not in str(points) else f"- ⚡ **XP Points:** {points}")

    lines.append("")
    lines.append("*(Updated automatically via GitHub Actions)*")
    return "\n".join(lines)

def update_readme(content):
    readme_path = "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()

        pattern = r"(<!-- START_SECTION:mslearn -->)(.*?)(<!-- END_SECTION:mslearn -->)"
        if not re.search(pattern, readme, flags=re.DOTALL):
            print("Warning: Anchor tags not found.")
            return

        replacement = f"\\1\n\n{content}\n\n\\3"
        updated = re.sub(pattern, replacement, readme, flags=re.DOTALL)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated)

        print("README.md successfully updated.")
    except FileNotFoundError:
        print("README.md not found.")

if __name__ == "__main__":
    stats = fetch_profile_stats()
    if stats and (stats.get("badges") or stats.get("trophies")):
        md = build_markdown(stats)
        update_readme(md)
    else:
        print(f"Stats fetched: {stats}. Could not extract non-zero stats from public page.")
