# GitHub Maintainer Bot

An intelligent AI-powered GitHub repository maintenance bot that automates contributor support, detects duplicate issues, learns from interactions, and provides comprehensive repository health monitoring through email notifications.

## 🚀 Features

- **📧 Email Notification Processing**: Automatically processes GitHub PR and issue notifications
- **🔍 Duplicate Issue Detection**: Intelligently groups similar bug reports using advanced similarity scoring
- **🧠 FAQ Learning System**: Builds knowledge base from past interactions for better future responses
- **⏰ Neglected PR Monitoring**: Tracks PRs and alerts maintainers for items needing attention (>7 days)
- **📊 Weekly Health Reports**: Generates comprehensive repository status reports with actionable insights

## 📋 Prerequisites

Before setting up the project, ensure you have:

- **Python 3.8+** installed on your system
- **Git** for version control
- **An AgentMail Account** - [Contact AgentMail](mailto:contact@agentmail.to) for API access
- **OpenAI API Key** - [Get yours here](https://platform.openai.com/api-keys)
- **ngrok Account** - [Sign up at ngrok.com](https://ngrok.com/) for webhook tunneling

## 🛠️ Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/YourUsername/AgentMail-PR_Bot.git
cd Github-maintainer-agent
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your configuration:**
   ```env
   # AgentMail Configuration
   AGENTMAIL_API_KEY=your_agentmail_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here

   # Inbox Configuration
   INBOX_USERNAME=maintainer
   WEBHOOK_DOMAIN=your-custom-domain.ngrok-free.app

   # Ngrok Configuration
   NGROK_AUTHTOKEN=your_ngrok_authtoken_here

   # Repository Monitoring
   TARGET_GITHUB_REPO=YourUsername/YourRepository
   REPORT_TARGET_EMAIL=your-email@example.com

   # Monitoring Schedule (in seconds)
   MONITORING_INTERVAL=604800
   ```

## 🚀 Running the Bot

### Start the Bot

```bash
python main.py
```

### Expected Output

```
Starting Advanced GitHub Maintainer Bot...
Target Repository: owner/repository
Report Email: your-email@example.com
Setting up AgentMail infrastructure...
Inbox maintainer@agentmail.to ready
ngrok tunnel: https://your-domain.ngrok-free.app
Webhook configured: https://your-domain.ngrok-free.app/webhooks
Bot ready! Inbox: maintainer@agentmail.to
Features: GitHub notifications, repository monitoring, automated reports
Starting repository monitoring thread...
Repository monitoring active - reports every 10080 minutes
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
```

## 🧪 Testing the Bot

### Test 1: Email Response (Immediate)

1. Send a test email to your AgentMail inbox: `maintainer@agentmail.to`
2. Include GitHub-like content in the subject/body
3. Check terminal logs for webhook processing
4. Verify bot response in your email

### Test 2: Quick Health Report

For testing without waiting a week:

1. **Temporarily change monitoring interval:**
   ```bash
   # In .env file
   MONITORING_INTERVAL=120  # 2 minutes for testing
   ```

2. **Restart the bot**
3. **Wait 2 minutes** for the first report
4. **Check your configured email** for the health report
5. **Revert back to weekly:**
   ```bash
   MONITORING_INTERVAL=604800  # Back to 1 week
   ```

### Test 3: Duplicate Detection

1. Send an email with a bug report (e.g., "ImportError in main.py")
2. Send a similar issue with different wording
3. Second issue should be detected as duplicate
4. Verify consolidated response

### Test 4: GitHub Integration

1. **Configure GitHub Repository:**
   - Go to your repo → Settings → Notifications
   - Add `maintainer@agentmail.to` to notification emails
   
2. **Create test issue/PR** in your repository
3. **Monitor bot logs** for webhook processing
4. **Check for automated response** to contributor

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit changes: `git commit -m 'Add feature description'`
5. Push to branch: `git push origin feature-name`
6. Submit a pull request


