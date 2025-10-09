# Dinner Agent Example

An AI agent that automatically organizes group dinners by collecting RSVPs via email and booking restaurants through OpenTable.

## Features

- **Email-based RSVP Collection**: Collects replies from dinner participants via AgentMail
- **Smart Participant Tracking**: Stores names, emails, phones, and time preferences
- **Random Cuisine Selection**: Picks from Thai, Chinese, or Indian cuisine randomly
- **Automated Restaurant Search**: Uses web search to find suitable restaurants
- **OpenTable Booking**: Headless browser automation for reservation booking
- **Confirmation Management**: Captures booking confirmations and notifies all participants

## Requirements

- Python 3.11 or higher
- [AgentMail API key](https://agentmail.io)
- [OpenAI API key](https://platform.openai.com)
- [Browserbase API key](https://www.browserbase.com)
- [Ngrok account](https://ngrok.com) (for receiving webhooks)

## Setup

### Ngrok

1. Sign up for a free Ngrok account at [ngrok.com](https://ngrok.com)
2. Get your Ngrok auth token
3. Claim your free static domain

### Browserbase

1. Sign up at [browserbase.com](https://www.browserbase.com)
2. Create a new project
3. Get your API key and project ID

### Config

Create a `.env` file with the following content:

```sh
AGENTMAIL_API_KEY=your-agentmail-api-key
OPENAI_API_KEY=your-openai-api-key
NGROK_AUTHTOKEN=your-ngrok-authtoken
BROWSERBASE_API_KEY=your-browserbase-api-key
BROWSERBASE_PROJECT_ID=your-browserbase-project-id

INBOX_USERNAME=dinner-agent
WEBHOOK_DOMAIN=your-webhook-domain
```

Export environment variables in the `.env` file:

```sh
export $(grep -v '^#' .env | xargs)
```

### AgentMail

Create an inbox:

```sh
curl -X POST https://api.agentmail.to/v0/inboxes \
     -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
     -H "Content-Type: application/json" \
     -d "{
  \"username\": \"$INBOX_USERNAME\",
  \"display_name\": \"Dinner Agent\"
}"
```

Create a webhook:

```sh
curl -X POST https://api.agentmail.to/v0/webhooks \
     -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
     -H "Content-Type: application/json" \
     -d "{
  \"url\": \"https://$WEBHOOK_DOMAIN/webhooks\"
}"
```

### Install

```sh
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install .
```

## Usage

1. Start the dinner agent:

```sh
python main.py
```

2. Send an email to `dinner-agent@agentmail.to` with dinner details:

```
Subject: Group Dinner Planning

Hi Dinner Agent,

Please organize a dinner for our team. We need reservations for 8 people.

Organizer: John Smith
Phone: (555) 123-4567
Preferred day: Saturday
Preferred time: 7:00 PM

Please wait for everyone to confirm before booking.

Thanks!
```

3. The agent will:
   - Wait for RSVP confirmations
   - Once enough people confirm, randomly select a cuisine
   - Search for suitable restaurants
   - Book a reservation on OpenTable
   - Send confirmation details to all participants

## How It Works

1. **Email Reception**: The agent listens for incoming emails via AgentMail webhooks
2. **RSVP Collection**: Tracks participant responses and stores their preferences
3. **Booking Trigger**: Once the minimum number of confirmations is reached
4. **Restaurant Selection**: Randomly picks cuisine and searches for restaurants
5. **OpenTable Automation**: Uses Stagehand to navigate and book reservations
6. **Confirmation**: Captures booking details and notifies all participants

## Example Email Flow

### Initial Request
```
To: dinner-agent@agentmail.to
Subject: Team Dinner - Saturday 7 PM

Please organize dinner for 6 people.
Organizer: Sarah Johnson, sarah@company.com, (555) 987-6543
Preferred: Saturday 7 PM
```

### Participant Confirmations
```
To: dinner-agent@agentmail.to
Subject: Re: Team Dinner Invitation

I can make it! 
- Mike Chen, mike@company.com, (555) 111-2222
```

### Final Confirmation
```
From: dinner-agent@agentmail.to
Subject: Dinner Confirmed - Thai Restaurant Booking

Great news! Your dinner is confirmed:

🍽️ Restaurant: Thai Garden Restaurant
📅 Date: Saturday, January 20th
⏰ Time: 7:00 PM
👥 Party Size: 6 people
📞 Confirmation: #ABC123

Address: 123 Main St, San Francisco, CA
Phone: (415) 555-0123

Confirmation URL: https://opentable.com/booking/abc123

See you there!
```

## Architecture

- `main.py`: Main application entry point
- `dinner_agent.py`: Core agent logic and email processing
- `restaurant_booking.py`: OpenTable automation with Stagehand
- `participant_tracker.py`: RSVP collection and storage
- `cuisine_selector.py`: Random cuisine selection logic
