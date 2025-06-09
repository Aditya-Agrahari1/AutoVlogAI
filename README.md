# 🌐 Echo Mind — AI-Driven Automated Blogging Platform

Echo Mind is a cutting-edge AI-powered blogging platform that autonomously generates, formats, and publishes insightful articles using the power of LLMs, Google GenAI, and real-time data. Built using **FastAPI**, it features a modern UI, automated workflows, and email contact integration via Gmail SMTP.

> 🚀 “Let the mind echo ideas — automatically.”

---

## 🌐 Live Preview

Check out the live website here: [EchoMind](https://echomind-lvlj.onrender.com)

---
## 🧠 What It Does

- **Fetches** the latest updates from trusted sources via **NewsAPI**
- **Summarizes & styles** them using **Google Gemini AI**
- **Formats** each into Markdown with hashtags, metadata, and media
- **Publishes** it as a new blog post — fully autonomous!

---

## 📚 Niches Covered

- 💻 **Tech News**  
- 🤖 **AI & Startup Updates**  
- 🧘‍♂️ **Self-Awareness & Meditation**

 ---

 ## 🖼️ Each Article Includes

- 🎯 Catchy blog title & SEO meta-description  
- ✍️ Well-structured summary with emojis & hashtags  
- 🖼️ Image + shareable snippet  
- ⏱️ Created & posted daily (auto-scheduled support coming soon!)


## 🧠 Features

- ✨ **AI-Powered Article Generation**
  - Fetches current trends and news
  - Summarizes and formats using Google GenAI

- 🎨 **Markdown to Blog Conversion**
  - Converts AI-generated markdown into beautiful HTML

- 📬 **Contact Form with Email Integration**
  - Users can send messages using a styled form (Gmail SMTP backend)

- 📁 **Fully Automated Blog Upload**
  - Content generated, formatted, and published without manual work

- ⚙️ **MongoDB + Cloudinary Support**
  - Store content and assets dynamically  

- 🔐 **Admin Panel**
  - To manage blog posts - generating, editing, or deleting vlogs
---

## 🔐 Admin Panel

An admin panel is available to manage blog posts — including generating, editing, or deleting vlogs.

🔗 Access it here: http://localhost:8000/admin/generate  
🧾 The panel is protected by a username/password login for security.


## 🚧 Tech Stack

| Layer       | Tech                         |
|------------|------------------------------|
| Backend     | FastAPI, Uvicorn             |
| Templates   | Jinja2 + TailwindCSS         |
| AI Engine   | Google Gemini AI (`google.generativeai`)  
| News Feed   | [NewsAPI.org](https://newsapi.org)  
| Email       | Gmail SMTP for Contact Form  |
| DB / Media  | MongoDB (motor) + Cloudinary |
| Deployment  | Render.com                   |

---

## 🛠️ Local Setup

### 1. Clone the repository

 git clone https://github.com/Aditya-Agrahari1/AutoVlogAI.git
 
 cd AutoVlogAI

2. Create a virtual environment
python -m venv venv
source venv/bin/activate    # For Linux/macOS
venv\Scripts\activate       # For Windows

3. Install dependencies
pip install -r requirements.txt

4. Setup .env file

5. Run the server
uvicorn src.main:app --reload
Then open http://localhost:8000 in your browser.

## 📨 Contact Form Support
✅ Sends user queries via Gmail SMTP

✅ Works with Render & other deployment platforms

✅ Shows user-friendly confirmation popup


## 🌍 Deploying to Render
Add the following Start Command in Render:

uvicorn main:app --host 0.0.0.0 --port $PORT

Set your .env variables (Gmail, NewsAPI, etc.) in Render's environment settings.

## 🧑‍💻 Contributing
Love automation + AI + content?

Contributions, issues, and suggestions are welcome!

Fork this repo

Make changes

Submit a pull request


## 📜 License
Licensed under the MIT License.

Free to use, build upon, and innovate!

## 🔗 Connect
Made with ❤️ by Aditya Agrahari

📩 Email: techVeltrix@gmail.com

📲 Telegram: @xKiteretsu

🧘‍♂️ "Echo the mind. Automate the grind."
