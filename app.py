import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask
import google.generativeai as genai

# Flask App
app = Flask(__name__)

# ------------------ CONFIG ------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SEARCH_KEYWORDS = "php developer, data analyst"
FILTER_KEYWORDS = ["php", "backend", "wordpress", "data analysis", "mysql", "core php"]
CHECK_INTERVAL = 60 * 15  # 15 minutes

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
seen_links = set()

# --------------------------------------------

def fetch_jobs(keyword=SEARCH_KEYWORDS):
    url = f"https://www.freelancer.com/jobs/{keyword.replace(' ', '-')}/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    jobs = []
    for job in soup.select(".JobSearchCard-item"):
        title_tag = job.select_one(".JobSearchCard-primary-heading a")
        if not title_tag:
            continue
        title = title_tag.text.strip()
        link = "https://www.freelancer.com" + title_tag["href"]
        if link in seen_links:
            continue
        seen_links.add(link)
        desc = job.select_one(".JobSearchCard-primary-description")
        desc_text = desc.text.strip() if desc else "No description"
        jobs.append({"title": title, "link": link, "description": desc_text})
    return jobs

def filter_jobs(jobs):
    return [job for job in jobs if any(word.lower() in job["description"].lower() for word in FILTER_KEYWORDS)]

def generate_proposal(job):
    prompt = f"""
Write a freelance job proposal based on the job below:

Title: {job['title']}
Description: {job['description']}

Guidelines:
- Start with: "Respected Sir/Madam,"
- Use 2 short paragraphs:
  • Paragraph 1: Show understanding of the client's need and relate your relevant project experience.
  • Paragraph 2: Highlight specific PHP, API, backend, or data skills and real impact from your past work.
- Limit each paragraph to a maximum of 70 words.
- End with:

Sincerely,  
Abhiram Jayani  
📞 8520997742  
📧 jayaniabhiram@gmail.com  
🔘 [Portfolio](https://jayaniabhiram.vercel.app)  
🔘 [LinkedIn](https://linkedin.com/in/jayaniabhiram)

Avoid generic statements. Make the proposal relevant and powerful.
"""
    print("🧠 Generating custom proposal...")
    try:
        response = model.generate_content(prompt)
        print("✅ Proposal received from Gemini.\n")
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return f"⚠️ Failed to generate proposal: {e}"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("❌ Telegram error:", response.text)
        else:
            print("📩 Sent to Telegram")
    except Exception as e:
        print("Telegram Exception:", e)

def bot_loop():
    while True:
        print("🔍 Checking Freelancer jobs...")
        jobs = fetch_jobs()
        filtered_jobs = filter_jobs(jobs)
        for job in filtered_jobs:
            print(f"📋 Job found: {job['title']}")
            proposal = generate_proposal(job)
            encoded_proposal = requests.utils.quote(proposal)
            msg = f"""📌 *New Job Found!*

*{job['title']}*
🔗 {job['link']}

📝 *Proposal:*
{proposal}

🔘 [📋 Copy Proposal](https://copy-text.now.sh/?text={encoded_proposal})
"""
            send_telegram(msg)
            print(f"✅ Job '{job['title']}' sent.\n")
        print(f"⏱ Waiting {CHECK_INTERVAL // 60} minutes for next check...\n")
        time.sleep(CHECK_INTERVAL)

# ----------------- WEB APP ------------------

@app.route("/")
def status():
    return "✅ Freelancer Auto Proposal Bot is running!"

@app.route("/run")
def manual_run():
    threading.Thread(target=bot_loop, daemon=True).start()
    return "🚀 Bot started manually in background!"

# --------------- RUN FLASK APP --------------

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
