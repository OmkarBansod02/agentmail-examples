import os
import re
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from agentmail import AgentMail
from participant_tracker import ParticipantTracker, DinnerEvent
from cuisine_selector import CuisineSelector
from restaurant_booking import RestaurantBooking


class DinnerAgent:
    """Main dinner agent that handles email processing and booking coordination"""
    
    def __init__(self):
        self.agentmail = AgentMail()
        self.participant_tracker = ParticipantTracker()
        self.cuisine_selector = CuisineSelector()
        self.restaurant_booking = RestaurantBooking()
        self.inbox = f"{os.getenv('INBOX_USERNAME')}@agentmail.to"
        self.min_confirmations = int(os.getenv('MIN_CONFIRMATIONS', 4))
        self.location = os.getenv('LOCATION', 'San Francisco')
    
    def process_email(self, email_data: Dict) -> str:
        """Process incoming email and determine response"""
        from_email = email_data["from"]
        subject = email_data["subject"]
        body = email_data["text"]
        
        print(f"Processing email from: {from_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body[:200]}...")
        
        # Determine if this is a new dinner request or an RSVP
        if self._is_new_dinner_request(subject, body):
            return self._handle_new_dinner_request(from_email, subject, body)
        elif self._is_rsvp_response(subject, body):
            return self._handle_rsvp_response(from_email, subject, body)
        else:
            return self._handle_general_inquiry(from_email, subject, body)
    
    def _is_new_dinner_request(self, subject: str, body: str) -> bool:
        """Check if email is a new dinner planning request"""
        keywords = [
            'organize dinner', 'plan dinner', 'group dinner', 'team dinner',
            'book restaurant', 'make reservation', 'dinner for'
        ]
        
        combined_text = f"{subject} {body}".lower()
        return any(keyword in combined_text for keyword in keywords)
    
    def _is_rsvp_response(self, subject: str, body: str) -> bool:
        """Check if email is an RSVP response"""
        rsvp_keywords = [
            'i can make it', 'count me in', 'i\'ll be there', 'yes, i can attend',
            'i\'m in', 'i can come', 'attending', 'confirmed'
        ]
        
        combined_text = f"{subject} {body}".lower()
        return any(keyword in combined_text for keyword in rsvp_keywords)
    
    def _handle_new_dinner_request(self, from_email: str, subject: str, body: str) -> str:
        """Handle new dinner planning request"""
        try:
            # Extract organizer information
            organizer_info = self._extract_organizer_info(from_email, body)
            
            # Extract dinner details
            dinner_details = self._extract_dinner_details(body)
            
            # Create new dinner event
            event_id = self.participant_tracker.create_dinner_event(
                organizer_email=organizer_info['email'],
                organizer_name=organizer_info['name'],
                organizer_phone=organizer_info['phone'],
                min_confirmations=dinner_details.get('party_size', self.min_confirmations),
                preferred_day=dinner_details.get('day'),
                preferred_time=dinner_details.get('time'),
                location=dinner_details.get('location', self.location)
            )
            
            print(f"Created new dinner event: {event_id}")
            
            # Generate invitation emails to send to others
            invitation_message = self._generate_invitation_message(organizer_info, dinner_details)
            
            return f"""Thanks for organizing the group dinner, {organizer_info['name']}!

I've created a new dinner event and I'm ready to collect RSVPs from your group.

Here are the details I have:
- Party size: {dinner_details.get('party_size', self.min_confirmations)} people
- Preferred day: {dinner_details.get('day', 'flexible')}
- Preferred time: {dinner_details.get('time', 'flexible')}
- Location: {dinner_details.get('location', self.location)}

I'll wait for at least {dinner_details.get('party_size', self.min_confirmations)} people to confirm before booking a restaurant.

Please have your guests email me at {self.inbox} to confirm their attendance.

Sample RSVP message they can send:
"{invitation_message}"

I'll automatically:
1. Collect everyone's RSVPs and preferences
2. Select a random cuisine (Thai, Chinese, or Indian)
3. Find and book a suitable restaurant on OpenTable
4. Send confirmation details to everyone

Let the RSVPs begin! 🍽️"""
            
        except Exception as e:
            print(f"Error handling dinner request: {e}")
            return f"""I'd love to help organize your dinner! However, I need a bit more information.

Please include:
- Your name and phone number
- How many people will be attending
- Preferred day and time
- Any location preferences

Example format:
"Hi Dinner Agent,
Please organize a dinner for 6 people.
Organizer: John Smith, (555) 123-4567
Preferred: Saturday 7 PM
Location: San Francisco

Thanks!"

Then I'll coordinate with everyone and make the reservation! 🍽️"""
    
    def _handle_rsvp_response(self, from_email: str, subject: str, body: str) -> str:
        """Handle RSVP confirmation"""
        try:
            # Extract participant information
            participant_info = self._extract_participant_info(from_email, body)
            
            # Find active dinner events
            active_events = self.participant_tracker.get_active_events()
            
            if not active_events:
                return """I don't currently have any active dinner events. 

If you're trying to RSVP for a dinner, please ask the organizer to create a new dinner request first.

Thanks! 🍽️"""
            
            # For simplicity, add to the most recent event
            event_id = list(active_events.keys())[-1]
            
            # Add participant confirmation
            success = self.participant_tracker.add_participant_confirmation(
                event_id=event_id,
                participant_email=participant_info['email'],
                participant_name=participant_info['name'],
                participant_phone=participant_info.get('phone', ''),
                preferred_day=participant_info.get('preferred_day'),
                preferred_time=participant_info.get('preferred_time')
            )
            
            if not success:
                return "Sorry, I couldn't process your RSVP. Please try again or contact the organizer."
            
            confirmed_count = self.participant_tracker.get_confirmed_count(event_id)
            event = self.participant_tracker.get_event(event_id)
            
            response = f"""Thanks for confirming, {participant_info['name']}! 

Current RSVPs: {confirmed_count}/{event.min_confirmations} people confirmed

"""
            
            # Check if we're ready to book
            if self.participant_tracker.is_ready_to_book(event_id):
                response += "🎉 We have enough confirmations! I'm now booking the restaurant...\n\n"
                
                # Trigger booking process in a new thread with its own event loop
                import threading
                def run_booking():
                    try:
                        asyncio.run(self._book_restaurant_for_event(event_id))
                    except Exception as e:
                        print(f"Error in booking thread: {e}")
                
                booking_thread = threading.Thread(target=run_booking, daemon=True)
                booking_thread.start()
                
                response += "I'll send confirmation details to everyone once the booking is complete!"
            else:
                needed = event.min_confirmations - confirmed_count
                response += f"Still waiting for {needed} more confirmations before I can book the restaurant."
            
            return response
            
        except Exception as e:
            print(f"Error handling RSVP: {e}")
            return f"""Thanks for your RSVP! I've noted your confirmation.

If you'd like to include specific preferences, you can mention:
- Your preferred day (e.g., Saturday)
- Your preferred time (e.g., 7 PM)
- Your phone number

I'll keep track of everyone's responses and book once we have enough confirmations! 🍽️"""
    
    def _handle_general_inquiry(self, from_email: str, subject: str, body: str) -> str:
        """Handle general inquiries about dinner agent"""
        return f"""Hi there! I'm the Dinner Agent 🍽️

I help organize group dinners by:
• Collecting RSVPs from your group
• Randomly selecting cuisine (Thai, Chinese, or Indian)
• Finding and booking restaurants on OpenTable
• Sending confirmation details to everyone

To get started, send me a dinner request like:
"Please organize dinner for 6 people. Organizer: [Your Name], [Phone]. Preferred: Saturday 7 PM"

Or if you're RSVPing: "I can make it! - [Your Name]"

Need help? Just reply with your questions!"""
    
    def _extract_organizer_info(self, from_email: str, body: str) -> Dict:
        """Extract organizer information from email"""
        info = {'email': from_email, 'name': '', 'phone': ''}
        
        # Extract name
        name_patterns = [
            r'organizer:\s*([^,\n]+)',
            r'name:\s*([^,\n]+)',
            r'i\'m\s+([^,\n]+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                info['name'] = match.group(1).strip()
                break
        
        # If no name found, try to extract from email
        if not info['name']:
            info['name'] = from_email.split('@')[0].replace('.', ' ').title()
        
        # Extract phone
        phone_pattern = r'[\(]?(\d{3})[\)]?[-.\s]?(\d{3})[-.\s]?(\d{4})'
        phone_match = re.search(phone_pattern, body)
        if phone_match:
            info['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
        
        return info
    
    def _extract_participant_info(self, from_email: str, body: str) -> Dict:
        """Extract participant information from RSVP email"""
        info = {'email': from_email, 'name': ''}
        
        # Extract name (participant might sign their name)
        name_patterns = [
            r'[-–]\s*([^,\n]+)$',  # Ends with "- Name"
            r'thanks,\s*([^,\n]+)',
            r'regards,\s*([^,\n]+)',
            r'best,\s*([^,\n]+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
            if match:
                info['name'] = match.group(1).strip()
                break
        
        # If no name found, extract from email
        if not info['name']:
            info['name'] = from_email.split('@')[0].replace('.', ' ').title()
        
        # Extract preferences
        if 'saturday' in body.lower():
            info['preferred_day'] = 'Saturday'
        elif 'sunday' in body.lower():
            info['preferred_day'] = 'Sunday'
        # Add more day patterns as needed
        
        # Extract time preferences
        time_pattern = r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))'
        time_match = re.search(time_pattern, body, re.IGNORECASE)
        if time_match:
            info['preferred_time'] = time_match.group(1)
        
        return info
    
    def _extract_dinner_details(self, body: str) -> Dict:
        """Extract dinner details from organizer email"""
        details = {}
        
        # Extract party size
        party_patterns = [
            r'dinner for (\d+)',
            r'(\d+) people',
            r'party of (\d+)',
        ]
        
        for pattern in party_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                details['party_size'] = int(match.group(1))
                break
        
        # Extract day preference
        day_patterns = [
            r'preferred.*?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        ]
        
        for pattern in day_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                details['day'] = match.group(1).title()
                break
        
        # Extract time preference
        time_pattern = r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))'
        time_match = re.search(time_pattern, body, re.IGNORECASE)
        if time_match:
            details['time'] = time_match.group(1)
        
        return details
    
    def _generate_invitation_message(self, organizer_info: Dict, dinner_details: Dict) -> str:
        """Generate sample invitation message"""
        day = dinner_details.get('day', 'this weekend')
        time = dinner_details.get('time', 'evening')
        
        return f"Hi! I can make it for dinner {day} around {time}. Looking forward to it! - [Your Name]"
    
    async def _book_restaurant_for_event(self, event_id: str):
        """Book restaurant for a dinner event (async)"""
        try:
            event = self.participant_tracker.get_event(event_id)
            if not event or event.booked:
                return
            
            print(f"Starting booking process for event {event_id}")
            
            # Get common preferences
            preferred_day, preferred_time = self.participant_tracker.get_most_common_preferences(event_id)
            confirmed_count = self.participant_tracker.get_confirmed_count(event_id)
            
            # Select cuisine and restaurant
            cuisine, restaurant_info = self.cuisine_selector.get_restaurant_recommendation(
                location=event.location,
                day=preferred_day or 'Saturday',
                time=preferred_time or '7:00 PM',
                party_size=confirmed_count
            )
            
            print(f"Selected {cuisine} cuisine, restaurant: {restaurant_info['name']}")
            
            # Book reservation
            booking_result = await self.restaurant_booking.book_opentable_reservation(
                restaurant_info=restaurant_info,
                party_size=confirmed_count,
                date=preferred_day or 'Saturday',
                time=preferred_time or '7:00 PM',
                organizer_name=event.organizer.name,
                organizer_email=event.organizer.email
            )
            
            if booking_result.get('success'):
                # Mark as booked
                self.participant_tracker.mark_as_booked(
                    event_id=event_id,
                    restaurant_name=booking_result['restaurant_name'],
                    confirmation_code=booking_result['confirmation_number'],
                    booking_url=booking_result.get('confirmation_url', ''),
                    cuisine=cuisine
                )
                
                # Send confirmation emails to all participants
                await self._send_booking_confirmations(event_id, booking_result, cuisine)
                
                print(f"Successfully booked and notified participants for event {event_id}")
            else:
                print(f"Booking failed for event {event_id}: {booking_result.get('error')}")
                await self._send_booking_failure_notification(event_id, booking_result.get('error'))
                
        except Exception as e:
            print(f"Error in booking process: {e}")
            await self._send_booking_failure_notification(event_id, str(e))
    
    async def _send_booking_confirmations(self, event_id: str, booking_result: Dict, cuisine: str):
        """Send booking confirmation emails to all participants"""
        try:
            event = self.participant_tracker.get_event(event_id)
            participant_emails = self.participant_tracker.get_all_participant_emails(event_id)
            
            confirmation_message = f"""🎉 Great news! Your dinner is confirmed!

Restaurant: {booking_result['restaurant_name']} ({cuisine} Cuisine)
Date: {booking_result['date']}
Time: {booking_result['time']}
Party Size: {booking_result['party_size']} people
Confirmation: #{booking_result['confirmation_number']}

"""
            
            if booking_result.get('confirmation_url'):
                confirmation_message += f"Confirmation URL: {booking_result['confirmation_url']}\n\n"
            
            confirmation_message += """Looking forward to seeing everyone there! 🍽️

If you need to make any changes, please contact the restaurant directly or reply to this email.

Bon appétit!
- Dinner Agent"""
            
            # Send to all participants
            for email in participant_emails:
                self.agentmail.inboxes.messages.send(
                    inbox_id=self.inbox,
                    to=[email],
                    subject=f"Dinner Confirmed - {booking_result['restaurant_name']}",
                    text=confirmation_message
                )
                
        except Exception as e:
            print(f"Error sending confirmations: {e}")
    
    async def _send_booking_failure_notification(self, event_id: str, error_message: str):
        """Send notification when booking fails"""
        try:
            participant_emails = self.participant_tracker.get_all_participant_emails(event_id)
            
            failure_message = f"""Sorry, I encountered an issue while booking the restaurant.

Error: {error_message}

Please try booking manually or contact me with alternative preferences. I'll do my best to help arrange your dinner!

- Dinner Agent"""
            
            for email in participant_emails:
                self.agentmail.inboxes.messages.send(
                    inbox_id=self.inbox,
                    to=[email],
                    subject="Dinner Booking Issue - Manual Action Needed",
                    text=failure_message
                )
                
        except Exception as e:
            print(f"Error sending failure notifications: {e}")
