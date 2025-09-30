import os
import asyncio
from threading import Thread
from dotenv import load_dotenv

import ngrok
from flask import Flask, request, Response

from dinner_agent import DinnerAgent

load_dotenv()

# Configuration
port = 8080
domain = os.getenv("WEBHOOK_DOMAIN")
inbox = f"{os.getenv('INBOX_USERNAME')}@agentmail.to"

# Initialize services
listener = ngrok.forward(port, domain=domain, authtoken_from_env=True)
app = Flask(__name__)
dinner_agent = DinnerAgent()

print(f"""
🍽️  Dinner Agent Starting...

Inbox: {inbox}
Webhook Domain: {domain}
Minimum Confirmations: {os.getenv('MIN_CONFIRMATIONS', 4)}
Location: {os.getenv('LOCATION', 'San Francisco')}

Ready to organize group dinners!
""")


@app.route("/webhooks", methods=["POST"])
def receive_webhook():
    """Receive AgentMail webhook and process email"""
    Thread(target=process_webhook, args=(request.json,)).start()
    return Response(status=200)


def process_webhook(payload):
    """Process incoming email webhook"""
    try:
        email = payload["message"]
        
        prompt = f"""
From: {email["from"]}
Subject: {email["subject"]}
Body:
{email["text"]}
"""
        print(f"\n📧 New Email Received:")
        print(f"From: {email['from']}")
        print(f"Subject: {email['subject']}")
        print("-" * 50)
        
        # Process email with dinner agent
        response = dinner_agent.process_email(email)
        
        print(f"\n🤖 Agent Response:")
        print(response)
        print("-" * 50)
        
        # Send reply
        print(f"📤 Sending reply to {email['from']}...")
        dinner_agent.agentmail.inboxes.messages.reply(
            inbox_id=inbox,
            message_id=email["message_id"],
            text=response
        )
        print("✅ Reply sent successfully\n")
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        
        # Send error response
        try:
            error_message = """Sorry, I encountered an error processing your request. 

Please try again or contact support if the issue persists.

- Dinner Agent 🍽️"""
            
            dinner_agent.agentmail.inboxes.messages.reply(
                inbox_id=inbox,
                message_id=email["message_id"],
                text=error_message
            )
        except Exception as reply_error:
            print(f"Failed to send error reply: {reply_error}")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dinner-agent",
        "inbox": inbox,
        "active_events": len(dinner_agent.participant_tracker.get_active_events())
    }


@app.route("/status", methods=["GET"])  
def status():
    """Get current dinner agent status"""
    try:
        active_events = dinner_agent.participant_tracker.get_active_events()
        
        status_info = {
            "inbox": inbox,
            "active_events": len(active_events),
            "min_confirmations": dinner_agent.min_confirmations,
            "location": dinner_agent.location,
            "events": []
        }
        
        # Add event details
        for event_id, event in active_events.items():
            confirmed_count = dinner_agent.participant_tracker.get_confirmed_count(event_id)
            status_info["events"].append({
                "event_id": event_id,
                "organizer": event.organizer.name,
                "confirmed_count": confirmed_count,
                "min_required": event.min_confirmations,
                "ready_to_book": confirmed_count >= event.min_confirmations,
                "created_at": event.created_at
            })
        
        return status_info
        
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    print(f"🚀 Starting Dinner Agent server on port {port}")
    print(f"📧 Send emails to: {inbox}")
    print(f"🔗 Webhook URL: https://{domain}/webhooks")
    print(f"📊 Status URL: https://{domain}/status")
    print(f"❤️  Health URL: https://{domain}/health")
    print("\n" + "="*60)
    
    app.run(port=port, debug=False)
