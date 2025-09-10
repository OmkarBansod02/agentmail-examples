# GitHub Maintainer Agent

A sophisticated AI agent that automates GitHub repository management through email notifications. The agent processes GitHub email notifications, provides automated responses to contributors, learns from interactions, detects duplicate issues, and generates comprehensive weekly health reports.

## Features

- **GitHub Notification Processing**: Automatically processes PR and issue notifications from GitHub
- **Duplicate Detection**: Intelligently groups similar bug reports and provides consolidated responses
- **FAQ Learning**: Learns from past interactions to provide better responses to common questions
- **Neglected PR Monitoring**: Tracks PRs and identifies those needing maintainer attention (>7 days)
- **Weekly Health Reports**: Generates comprehensive repository health reports with actionable insights
- **Web Search Integration**: Uses real-time web search for current repository intelligence

## Prerequisites

Before you start, make sure you have the following:
- Python 3.8+
- An [AgentMail API Key](mailto:contact@agentmail.to)
- An [OpenAI account](https://openai.com/) and API key
- An [ngrok account](https://ngrok.com/) and authtoken

## Step 1: Project Setup

First, let's set up your project directory and install the necessary dependencies.

1. Create a project folder and navigate into it:
```bash
mkdir github-maintainer-bot
cd github-maintainer-bot
```

2. Create a `requirements.txt` file with the following content:
```txt
openai
agentmail
agentmail-toolkit
flask
python-dotenv
pyngrok
ngrok
agents
requests
beautifulsoup4
```

3. Install the packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file to store your secret keys and configuration:
```env
# AgentMail Configuration
AGENTMAIL_API_KEY="your_agentmail_api_key"
OPENAI_API_KEY="your_openai_api_key"

# Inbox Configuration
INBOX_USERNAME="maintainer"
WEBHOOK_DOMAIN="your-ngrok-subdomain.ngrok-free.app"

# Ngrok
NGROK_AUTHTOKEN="your_ngrok_authtoken"

# Repository Monitoring
TARGET_GITHUB_REPO="YourUsername/YourRepository"
REPORT_TARGET_EMAIL="your-email@example.com"

# Monitoring Schedule (in seconds)
MONITORING_INTERVAL=604800
```

**Configuration Notes:**
- `WEBHOOK_DOMAIN` is your custom domain from your ngrok dashboard
- `INBOX_USERNAME` will be the email address for your agent (e.g., maintainer@agentmail.to)
- `TARGET_GITHUB_REPO` should be in format "owner/repository" (not full GitHub URL)
- `MONITORING_INTERVAL` is set to 604800 seconds (1 week) for production

## Step 2: Core Files Setup

### Create `main.py`
This is the main agent script that handles webhook processing and repository monitoring.

### Create `utils.py`
Contains utility functions for GitHub information extraction, duplicate detection, and email formatting.

### Create `System_prompt.txt`
Contains the system prompt that defines the agent's behavior and capabilities.

## Step 3: Agent Architecture

### Webhook Processing
The agent receives GitHub notifications via AgentMail webhooks and processes them based on type:
- **New PRs**: Welcome contributors with helpful checklists
- **New Issues**: Thank reporters and check for duplicates
- **Comments**: Provide technical guidance using learned knowledge
- **Reviews**: Coordinate between reviewers and contributors

### Duplicate Detection System
Advanced duplicate detection using multiple scoring factors:
- **Error Keywords**: Matches common error terms and exceptions
- **File Patterns**: Identifies common affected files
- **Function Patterns**: Detects similar function calls
- **Semantic Similarity**: Word overlap analysis

### Repository Monitoring
Automated monitoring thread that:
- Uses WebSearchTool for real-time repository intelligence
- Generates comprehensive HTML health reports
- Tracks metrics, security alerts, and community activity
- Sends weekly reports to configured email address

## Step 4: Run the Agent

Start your agent:
```bash
python main.py
```

You should see output similar to:
```
Starting Advanced GitHub Maintainer Bot...
Target Repository: YourUsername/YourRepository
Report Email: your-email@example.com
Setting up AgentMail infrastructure...
Inbox maintainer@agentmail.to ready
ngrok tunnel: https://your-domain.ngrok-free.app
Webhook configured: https://your-domain.ngrok-free.app/webhooks
Bot ready! Inbox: maintainer@agentmail.to
Features: GitHub notifications, repository monitoring, automated reports
Starting repository monitoring thread...
Repository monitoring active - reports every 10080 minutes
```

## Step 5: Test Your Agent

### Test Scenario 1: GitHub Notification Processing
1. Configure your GitHub repository to send notifications to `maintainer@agentmail.to`
2. Create a new issue or PR in your repository
3. Check your terminal logs for webhook processing
4. The agent should respond automatically to the contributor

### Test Scenario 2: Duplicate Issue Detection
1. Send an email with a bug report containing specific error messages
2. Send a similar issue with slightly different wording
3. The second issue should be detected as a duplicate
4. You should receive a consolidated response referencing the previous report

### Test Scenario 3: Weekly Health Report
For testing purposes, temporarily change `MONITORING_INTERVAL` to a smaller value (e.g., 120 seconds):

1. Update `.env`: `MONITORING_INTERVAL=120`
2. Restart the agent
3. Wait 2 minutes for the first report
4. Check your configured email for the comprehensive health report
5. Revert to weekly schedule: `MONITORING_INTERVAL=604800`

### Test Scenario 4: FAQ Learning
1. Send questions to the agent inbox
2. Reply to get responses and build the knowledge base
3. Send similar questions later to see learned responses applied

## Agent Capabilities

### Email Processing Features
- **GitHub Notification Analysis**: Extracts PR/issue numbers, authors, files changed
- **Context-Aware Responses**: Tailored responses based on notification type
- **Thread Continuity**: Maintains conversation context across email exchanges
- **HTML Email Formatting**: Professional email structure with proper formatting

### Intelligence Features
- **FAQ Knowledge Base**: Learns from past interactions and applies knowledge
- **Duplicate Grouping**: Advanced similarity scoring for issue deduplication
- **Neglected PR Tracking**: Identifies PRs needing attention after 7+ days
- **Web Search Integration**: Real-time repository intelligence gathering

### Monitoring Features
- **Repository Health Reports**: Comprehensive weekly status reports
- **Security Monitoring**: Alerts for vulnerabilities and dependency updates
- **Community Metrics**: Tracks contributor activity and engagement
- **Action Items**: Provides prioritized recommendations for maintainers

## Configuration Options

### Environment Variables
- `MONITORING_INTERVAL`: Report frequency in seconds (default: 604800 = 1 week)
- `TARGET_GITHUB_REPO`: Repository to monitor in "owner/repo" format
- `REPORT_TARGET_EMAIL`: Email address for automated reports
- `INBOX_USERNAME`: AgentMail inbox username (creates inbox@agentmail.to)

### Customization
- **System Prompt**: Edit `System_prompt.txt` to modify agent behavior
- **Duplicate Threshold**: Adjust similarity scoring in `utils.py`
- **FAQ Learning**: Configure question detection patterns
- **Report Template**: Customize HTML report structure in monitoring function

## Use Cases

### For Indie Developers
- **Email Noise Reduction**: Filters and summarizes GitHub notifications
- **Automated Onboarding**: Provides consistent contributor guidance
- **Health Monitoring**: Weekly insights into repository status
- **Duplicate Management**: Reduces redundant issue handling

### For Open Source Projects
- **Contributor Support**: 24/7 automated responses to common questions
- **Pattern Recognition**: Identifies recurring issues and themes
- **Maintainer Assistance**: Alerts for PRs needing review
- **Community Insights**: Tracks engagement and growth metrics

## Troubleshooting

### Common Issues
1. **Webhook Not Receiving**: Check ngrok tunnel and webhook URL configuration
2. **API Errors**: Verify AgentMail and OpenAI API keys are correct
3. **No Reports**: Ensure TARGET_GITHUB_REPO and REPORT_TARGET_EMAIL are set
4. **Duplicate Detection Not Working**: Check FAQ knowledge base population

### Debugging
- Enable debug logging by adding print statements
- Check ngrok dashboard for webhook delivery status
- Verify GitHub notification settings
- Test API connectivity with simple requests

## Security Considerations

- Store API keys in `.env` file (never commit to version control)
- Use ngrok authentication for webhook endpoint security
- Regularly rotate API keys
- Monitor agent responses for sensitive information exposure

---

You now have a fully automated GitHub maintainer agent that can handle notifications, learn from interactions, detect duplicates, and provide comprehensive repository insights!
