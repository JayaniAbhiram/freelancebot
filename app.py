import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

# ------------------ CONFIG ------------------
GEMINI_API_KEY = "AIzaSyCxfprGVUVUNumMNmYokQTUTbMzOhH8f7Q"
TELEGRAM_BOT_TOKEN = "7494080573:AAFlJhPVpNNvJrEt5ZS-t6brUAIrYnKmH_Q"
TELEGRAM_CHAT_ID = "1507855306"    # 🔁 Replace with your Telegram Chat ID

SEARCH_KEYWORDS = "php developer, data analyst"
FILTER_KEYWORDS = ["php", "backend", "wordpress, data analysis, mysql, core php"]
CHECK_INTERVAL = 60 * 15  # every 30 minutes

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

seen_links = set()
# ------------------------------------------------

# 🔍 Fetch jobs from Freelancer.com
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

# 🧠 Filter by keyword
def filter_jobs(jobs):
    return [job for job in jobs if any(word.lower() in job["description"].lower() for word in FILTER_KEYWORDS)]

# ✨ Generate a job-specific 2-paragraph proposal
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

# 📩 Send message via Telegram
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

# 🔁 Main loop
def main():
    print("🔍 Checking Freelancer jobs...")
    jobs = fetch_jobs()
    filtered_jobs = filter_jobs(jobs)
    for job in filtered_jobs:
        print(f"📋 Job found: {job['title']}")
        proposal = generate_proposal(job)
        msg = f"""📌 *New Job Found!*

*{job['title']}*
🔗 {job['link']}

📝 *Proposal:*
{proposal}
"""
        send_telegram(msg)
        print(f"✅ Job '{job['title']}' sent.\n")

# 🔂 Loop every CHECK_INTERVAL
if __name__ == "__main__":
    while True:
        main()
        print(f"⏱ Waiting {CHECK_INTERVAL // 60} minutes for next check...\n")
        time.sleep(CHECK_INTERVAL)
