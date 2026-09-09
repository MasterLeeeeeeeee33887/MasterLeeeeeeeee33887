import os
import re
import requests

 
SHARE_ID = os.environ.get("MS_LEARN_SHARE_ID")
API_URL = f"https://learn.microsoft.com/api/profiles/transcript/share/{SHARE_ID}?locale=en-us"

def fetch_achievements():
    response = requests.get(API_URL)
    if response.status_code != 200:
        print("Failed to fetch transcript")
        return None
    
    data = response.json()
    

    badges_count = data.get("badgesCount", 0) 
    trophies_count = data.get("trophiesCount", 0)

    markdown = (
        f"🏆 **Trophies:** {trophies_count} | 🏅 **Badges:** {badges_count}\n\n"
        f"*(Last updated automatically via GitHub Actions)*"
    )
    return markdown

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    updated_readme = re.sub(
        r"(?<=<!-- START_SECTION:mslearn -->\n).*?(?=\n<!-- END_SECTION:mslearn -->)",
        new_content,
        readme,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)

if __name__ == "__main__":
    content = fetch_achievements()
    if content:
        update_readme(content)
