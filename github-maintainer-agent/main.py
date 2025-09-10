"""
Open Source Maintainer Bot - Simple GitHub repository maintenance bot using AgentMail
"""

from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
from threading import Thread
import json
import time 
from datetime import datetime, timedelta

import ngrok
from flask import Flask, request, Response

from agentmail import AgentMail
from agentmail_toolkit.openai import AgentMailToolkit
from agents import WebSearchTool, Agent, Runner
from utils import extract_github_info, is_question, extract_sender_name, detect_duplicate_issue, group_duplicate_response

# Configuration
port = 8080
domain = os.getenv("WEBHOOK_DOMAIN")
inbox_username = os.getenv("INBOX_USERNAME", "maintainer")
inbox = f"{inbox_username}@agentmail.to"

# Repository monitoring configuration
target_github_repo = os.getenv("TARGET_GITHUB_REPO")
report_target_email = os.getenv("REPORT_TARGET_EMAIL")
monitoring_interval = int(os.getenv("MONITORING_INTERVAL", "1800"))  # Default 30 minutes

if not target_github_repo:
    print("\nWARNING: TARGET_GITHUB_REPO environment variable is not set.")
    print("The agent will not perform proactive repository monitoring.")
    print("Please set it in your .env file (e.g., TARGET_GITHUB_REPO='owner/repository')\n")

if not report_target_email:
    print("\nWARNING: REPORT_TARGET_EMAIL environment variable is not set.")
    print("The agent will not send automated reports.")
    print("Please set it in your .env file (e.g., REPORT_TARGET_EMAIL='your.email@example.com')\n")

# Initialize AgentMail
client = AgentMail()
app = Flask(__name__)

# Simple in-memory storage for basic FAQ learning and PR tracking
faq_knowledge = {}
pr_tracking = {}

def setup_infrastructure():
    """Initialize AgentMail inbox and webhook"""
    print("Setting up AgentMail infrastructure...")
    
    # Create inbox idempotently
    inbox_client_id = f"inbox-for-{inbox_username}"
    try:
        client.inboxes.create(
            username=inbox_username,
            client_id=inbox_client_id
        )
        print(f"Inbox {inbox} ready")
    except Exception as e:
        print(f"Failed to create inbox: {e}")
        return False
    
    # Setup ngrok tunnel
    listener = ngrok.forward(port, domain=domain, authtoken_from_env=True)
    print(f"ngrok tunnel: {listener.url()}")
    
    # Create webhook
    webhook_url = f"{listener.url()}/webhooks"
    webhook_client_id = f"webhook-for-{inbox_username}"
    try:
        client.webhooks.create(
            url=webhook_url,
            client_id=webhook_client_id,
            event_types=["message.received"],
            inbox_ids=[inbox],
        )
        print(f"Webhook configured: {webhook_url}")
    except Exception as e:
        print(f"Failed to create webhook: {e}")
        return False 
    
    return True

# Load system prompt from file
def load_system_prompt():
    """Load and format system prompt from System_prompt.txt"""
    try:
        with open('System_prompt.txt', 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Format with current configuration
        return prompt_template.format(
            inbox=inbox,
            target_github_repo=target_github_repo or 'Not configured',
            report_target_email=report_target_email or 'Not configured'
        )
    except FileNotFoundError:
        print("Warning: System_prompt.txt not found, using fallback instructions")
        return f"""
You are a GitHub Maintainer Bot that processes GitHub email notifications.
Your email is: {inbox}
Target Repository: {target_github_repo or 'Not configured'}
Report Email: {report_target_email or 'Not configured'}

Process GitHub notifications, provide helpful responses to contributors, 
learn from patterns, detect duplicates, and generate weekly health reports.
"""

instructions = load_system_prompt()

agent = Agent(
    name="Advanced GitHub Maintainer Bot",
    instructions=instructions,
    tools=AgentMailToolkit(client).get_tools() + [WebSearchTool()],
)

messages = []

@app.route("/webhooks", methods=["POST"])
def receive_webhook():
    """Handle incoming webhook from AgentMail"""
    print(f"Received webhook: {list(request.json.keys()) if request.is_json else 'Not JSON'}")
    Thread(target=process_webhook, args=(request.json,)).start()
    return Response(status=200)

def process_webhook(payload):
    """Process incoming email webhook - simplified with AgentMail native memory"""
    global messages, faq_knowledge, pr_tracking
    
    try:
        email = payload["message"]
        sender = email.get('from', '')
        subject = email.get('subject', '')
        body = email.get('text', '')
        thread_id = email.get('thread_id')  # AgentMail handles conversation threading
        
        print(f"Processing email from: {sender}, subject: {subject}")
        
        # Extract GitHub information for context
        github_info = extract_github_info(subject, body)
        sender_name = extract_sender_name(sender)
        
        # Simple PR tracking for neglect detection
        if github_info['is_pr'] and github_info['pr_number']:
            pr_key = f"{github_info['repo_name']}#{github_info['pr_number']}"
            pr_tracking[pr_key] = {
                'last_seen': datetime.now(),
                'subject': subject
            }
        
        # Enhanced duplicate detection for issues
        duplicate_info = None
        similar_context = ""
        
        if github_info['is_issue'] and faq_knowledge:
            # Use enhanced duplicate detection
            duplicate_info = detect_duplicate_issue(body, faq_knowledge)
            
            if duplicate_info:
                # Handle as duplicate - send consolidated response
                print(f"Duplicate issue detected with score: {duplicate_info['similarity_score']}")
                duplicate_response = group_duplicate_response(
                    sender_name, 
                    duplicate_info, 
                    github_info.get('repo_name', 'repository')
                )
                
                # Send duplicate response directly
                client.inboxes.messages.reply(
                    inbox_id=inbox, 
                    message_id=email["message_id"], 
                    html=duplicate_response
                )
                print(f"Duplicate issue response sent for message: {email['message_id']}")
                return  # Skip normal processing for duplicates
            
            # Fallback to simple similarity check
            for faq_key, faq_data in faq_knowledge.items():
                if any(word in body.lower() for word in faq_key.split() if len(word) > 3):
                    similar_context = f"\n\nSimilar question asked before: {faq_data['question'][:100]}..."
                    break
        
        # Build comprehensive prompt based on GitHub notification analysis
        if github_info['is_github']:
            prompt = f"""
            GitHub Notification Analysis:
            
            **Email Details:**
            From: {sender_name}
            Subject: {subject}
            
            **Parsed GitHub Info:**
            Repository: {github_info.get('repo_name', 'Unknown')}
            Type: {'PR' if github_info['is_pr'] else 'Issue' if github_info['is_issue'] else 'Comment/Review'}
            Number: #{github_info.get('pr_number') or github_info.get('issue_number', '?')}
            Action: {github_info.get('action', 'updated')}
            Author: {github_info.get('author', 'Unknown')}
            Title: {github_info.get('title', 'No title')}
            Summary: {github_info.get('summary', 'GitHub activity')}
            Files Changed: {', '.join(github_info.get('files_changed', [])[:5]) or 'None detected'}
            
            **Original Content:**
            {body}
            
            {similar_context}
            
            **Your Task:**
            As a GitHub maintainer bot, analyze this notification and provide an appropriate response:
            
            1. If this is a NEW PR/Issue: Welcome the contributor and provide helpful guidance
            2. If this is a COMMENT/QUESTION: Answer helpfully using any similar past knowledge
            3. If this is a DUPLICATE: Reference similar issues you've seen
            4. If this is NEGLECTED: Acknowledge the delay and provide status update
            
            Always format your response as HTML email and be professional but friendly.
            """
        else:
            # Non-GitHub email
            prompt = f"""
            Regular Email from {sender_name}:
            Subject: {subject}
            Content: {body}
            
            {similar_context}
            
            This doesn't appear to be a GitHub notification. Respond helpfully as a maintainer bot,
            but note that you primarily handle GitHub-related communications.
            """
        
        print("Processing with AgentMail thread context...")
        
        # Run agent (AgentMail toolkit handles thread context automatically)
        response = asyncio.run(Runner.run(agent, messages + [{"role": "user", "content": prompt}]))
        print("Response:", response.final_output)
        
        # Simple FAQ learning for questions
        if is_question(body):
            question_key = ' '.join(body.lower().split()[:10])  # First 10 words as key
            faq_knowledge[question_key] = {
                'question': body[:200],
                'count': faq_knowledge.get(question_key, {}).get('count', 0) + 1,
                'last_seen': datetime.now().isoformat()
            }
            print(f"FAQ learned. Total entries: {len(faq_knowledge)}")
        
        # Send reply via AgentMail (maintains thread automatically)
        client.inboxes.messages.reply(
            inbox_id=inbox, 
            message_id=email["message_id"], 
            html=response.final_output
        )
        print(f"Reply sent for message: {email['message_id']}")
        
        # Update agent messages for this session
        messages = response.to_input_list()
        
    except Exception as e:
        print(f"Error processing webhook: {e}")

def get_neglected_prs():
    """Simple check for PRs that haven't been seen recently"""
    neglected = []
    cutoff_date = datetime.now() - timedelta(days=7)
    
    for pr_key, pr_data in pr_tracking.items():
        if pr_data['last_seen'] < cutoff_date:
            days_old = (datetime.now() - pr_data['last_seen']).days
            neglected.append(f"{pr_key} ({days_old} days)")
    
    return neglected

# --- Repository Monitoring Logic ---

def monitor_repository():
    """Monitor target repository and generate periodic reports"""
    global messages
    
    if not target_github_repo or not report_target_email:
        print("[MONITOR] Repository monitoring disabled - missing configuration")
        return
    
    print(f"[MONITOR] Starting repository monitoring for {target_github_repo}")
    print(f"[MONITOR] Reports will be sent to {report_target_email} every {monitoring_interval} seconds")
    
    # Give the Flask app time to start
    time.sleep(5)
    
    report_count = 0
    
    while True:
        try:
            time.sleep(monitoring_interval)
            report_count += 1
            
            print(f"[MONITOR] Generating repository report #{report_count} for {target_github_repo}")
            
            prompt_for_report = f"""
REPOSITORY MONITORING TASK: Generate a comprehensive health report for repository '{target_github_repo}'.

Your goal is to create a detailed HTML email report and send it to {report_target_email} using the send_message tool.

Step 1: Gather Repository Intelligence
Use WebSearchTool to research the following aspects of '{target_github_repo}':
- Recent commits, releases, and development activity
- Open issues and pull request status
- Community engagement metrics (stars, forks, contributors)
- Security vulnerabilities or important updates
- Dependencies and maintenance status
- Recent discussions or community feedback

Step 2: Generate Repository Health Report
Based on your web search findings, create a comprehensive HTML email report with these sections:

**Email Structure:**
- Subject: "Repository Health Report: {target_github_repo} - [Current Date]"
- Recipient: {report_target_email}
- Inbox: {inbox}

**HTML Report Content:**
<h2>Repository Health Report</h2>
<h3>📊 Current Status</h3>
<p>[Repository overview and key metrics]</p>

<h3>🚀 Recent Activity</h3>
<ul>
<li>[Recent commits and releases]</li>
<li>[New features or improvements]</li>
</ul>

<h3>🐛 Issues & Pull Requests</h3>
<ul>
<li>[Open issues summary]</li>
<li>[PR status and review needed]</li>
<li>[Community contributions]</li>
</ul>

<h3>🔒 Security & Maintenance</h3>
<ul>
<li>[Security alerts or vulnerabilities]</li>
<li>[Dependency updates needed]</li>
<li>[Maintenance recommendations]</li>
</ul>

<h3>📈 Community Insights</h3>
<ul>
<li>[Growth metrics and engagement]</li>
<li>[Contributor activity]</li>
<li>[Community feedback]</li>
</ul>

<h3>⚡ Action Items</h3>
<ul>
<li>[Recommended immediate actions]</li>
<li>[Areas needing attention]</li>
</ul>

<p><strong>Report generated automatically by GitHub Maintainer Bot</strong></p>
<p><em>Next report scheduled in {monitoring_interval // 60} minutes</em></p>

**Important Requirements:**
- Use WebSearchTool first to gather current information
- Synthesize findings into actionable insights
- Do NOT include raw URLs in the email body
- Focus on actionable intelligence for maintainers
- Use proper HTML formatting throughout
- Call send_message tool to deliver the report

Your final output should confirm: "Repository health report #{report_count} sent to {report_target_email}"
"""
            
            print(f"[MONITOR] Processing repository analysis for report #{report_count}")
            
            # Generate report using agent with separate message context for monitoring
            monitoring_messages = []
            response = asyncio.run(Runner.run(agent, monitoring_messages + [{"role": "user", "content": prompt_for_report}]))
            
            print(f"[MONITOR] Agent response: {response.final_output}")
            
            if f"report #{report_count} sent" not in response.final_output.lower():
                print(f"[MONITOR_WARNING] Report may not have been sent successfully: {response.final_output}")
            else:
                print(f"[MONITOR] Successfully generated and sent repository report #{report_count}")
                
        except Exception as e:
            print(f"[MONITOR_ERROR] Error during repository monitoring: {e}")
            import traceback
            print(f"[MONITOR_ERROR] Traceback: {traceback.format_exc()}")
            # Continue monitoring despite errors
            continue

if __name__ == "__main__":
    print("Starting Advanced GitHub Maintainer Bot...")
    print(f"Target Repository: {target_github_repo or 'Not configured'}")
    print(f"Report Email: {report_target_email or 'Not configured'}")
    
    # Setup AgentMail infrastructure
    if not setup_infrastructure():
        print("Failed to setup infrastructure, exiting")
        exit(1)
    
    print(f"Bot ready! Inbox: {inbox}")
    print("The bot will respond to emails sent to this inbox.")
    print("Features: GitHub notifications, repository monitoring, automated reports")
    
    # Start repository monitoring thread if configured
    if target_github_repo and report_target_email:
        print(f"Starting repository monitoring thread...")
        monitoring_thread = Thread(target=monitor_repository)
        monitoring_thread.daemon = True  # Exit when main thread exits
        monitoring_thread.start()
        print(f"Repository monitoring active - reports every {monitoring_interval // 60} minutes")
    else:
        print("Repository monitoring disabled - check TARGET_GITHUB_REPO and REPORT_TARGET_EMAIL")
    
    # Start Flask app
    app.run(host="0.0.0.0", port=port, debug=False)
