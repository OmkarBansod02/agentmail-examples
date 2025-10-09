import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Participant:
    name: str
    email: str
    phone: str
    confirmed: bool = False
    preferred_day: Optional[str] = None
    preferred_time: Optional[str] = None
    confirmed_at: Optional[str] = None


@dataclass
class DinnerEvent:
    organizer: Participant
    participants: List[Participant]
    min_confirmations: int
    location: str = "San Francisco"
    cuisine: Optional[str] = None
    restaurant_name: Optional[str] = None
    booking_confirmation: Optional[str] = None
    booking_url: Optional[str] = None
    booked: bool = False
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class ParticipantTracker:
    def __init__(self, data_file: str = "dinner_events.json"):
        self.data_file = data_file
        self.events: Dict[str, DinnerEvent] = {}
        self.load_data()
    
    def load_data(self):
        """Load existing dinner events from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for event_id, event_data in data.items():
                        # Convert participant dicts back to Participant objects
                        organizer = Participant(**event_data['organizer'])
                        participants = [Participant(**p) for p in event_data['participants']]
                        
                        event = DinnerEvent(
                            organizer=organizer,
                            participants=participants,
                            min_confirmations=event_data['min_confirmations'],
                            location=event_data.get('location', 'San Francisco'),
                            cuisine=event_data.get('cuisine'),
                            restaurant_name=event_data.get('restaurant_name'),
                            booking_confirmation=event_data.get('booking_confirmation'),
                            booking_url=event_data.get('booking_url'),
                            booked=event_data.get('booked', False),
                            created_at=event_data.get('created_at')
                        )
                        self.events[event_id] = event
            except Exception as e:
                print(f"Error loading data: {e}")
    
    def save_data(self):
        """Save dinner events to JSON file"""
        try:
            data = {}
            for event_id, event in self.events.items():
                event_dict = asdict(event)
                data[event_id] = event_dict
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def create_dinner_event(self, organizer_email: str, organizer_name: str, 
                          organizer_phone: str, min_confirmations: int,
                          preferred_day: str = None, preferred_time: str = None,
                          location: str = "San Francisco") -> str:
        """Create a new dinner event"""
        organizer = Participant(
            name=organizer_name,
            email=organizer_email,
            phone=organizer_phone,
            confirmed=True,
            preferred_day=preferred_day,
            preferred_time=preferred_time,
            confirmed_at=datetime.now().isoformat()
        )
        
        event = DinnerEvent(
            organizer=organizer,
            participants=[],
            min_confirmations=min_confirmations,
            location=location
        )
        
        event_id = f"dinner_{len(self.events) + 1}_{int(datetime.now().timestamp())}"
        self.events[event_id] = event
        self.save_data()
        return event_id
    
    def add_participant_confirmation(self, event_id: str, participant_email: str,
                                   participant_name: str, participant_phone: str = "",
                                   preferred_day: str = None, preferred_time: str = None) -> bool:
        """Add or update a participant's confirmation"""
        if event_id not in self.events:
            return False
        
        event = self.events[event_id]
        
        # Check if participant already exists
        for i, participant in enumerate(event.participants):
            if participant.email.lower() == participant_email.lower():
                # Update existing participant
                event.participants[i].confirmed = True
                event.participants[i].confirmed_at = datetime.now().isoformat()
                if preferred_day:
                    event.participants[i].preferred_day = preferred_day
                if preferred_time:
                    event.participants[i].preferred_time = preferred_time
                self.save_data()
                return True
        
        # Add new participant
        participant = Participant(
            name=participant_name,
            email=participant_email,
            phone=participant_phone,
            confirmed=True,
            preferred_day=preferred_day,
            preferred_time=preferred_time,
            confirmed_at=datetime.now().isoformat()
        )
        
        event.participants.append(participant)
        self.save_data()
        return True
    
    def get_confirmed_count(self, event_id: str) -> int:
        """Get count of confirmed participants for an event"""
        if event_id not in self.events:
            return 0
        
        event = self.events[event_id]
        confirmed_count = 1  # Organizer is always confirmed
        confirmed_count += sum(1 for p in event.participants if p.confirmed)
        return confirmed_count
    
    def is_ready_to_book(self, event_id: str) -> bool:
        """Check if event has enough confirmations to book"""
        if event_id not in self.events:
            return False
        
        event = self.events[event_id]
        return (not event.booked and 
                self.get_confirmed_count(event_id) >= event.min_confirmations)
    
    def get_most_common_preferences(self, event_id: str) -> tuple:
        """Get the most common day and time preferences"""
        if event_id not in self.events:
            return None, None
        
        event = self.events[event_id]
        all_participants = [event.organizer] + [p for p in event.participants if p.confirmed]
        
        # Count day preferences
        day_counts = {}
        time_counts = {}
        
        for participant in all_participants:
            if participant.preferred_day:
                day_counts[participant.preferred_day] = day_counts.get(participant.preferred_day, 0) + 1
            if participant.preferred_time:
                time_counts[participant.preferred_time] = time_counts.get(participant.preferred_time, 0) + 1
        
        most_common_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
        most_common_time = max(time_counts.items(), key=lambda x: x[1])[0] if time_counts else None
        
        return most_common_day, most_common_time
    
    def mark_as_booked(self, event_id: str, restaurant_name: str, 
                      confirmation_code: str, booking_url: str, cuisine: str):
        """Mark event as booked with details"""
        if event_id not in self.events:
            return False
        
        event = self.events[event_id]
        event.booked = True
        event.restaurant_name = restaurant_name
        event.booking_confirmation = confirmation_code
        event.booking_url = booking_url
        event.cuisine = cuisine
        self.save_data()
        return True
    
    def get_all_participant_emails(self, event_id: str) -> List[str]:
        """Get all participant emails for an event"""
        if event_id not in self.events:
            return []
        
        event = self.events[event_id]
        emails = [event.organizer.email]
        emails.extend([p.email for p in event.participants if p.confirmed])
        return emails
    
    def get_event(self, event_id: str) -> Optional[DinnerEvent]:
        """Get event by ID"""
        return self.events.get(event_id)
    
    def get_active_events(self) -> Dict[str, DinnerEvent]:
        """Get all events that are not yet booked"""
        return {k: v for k, v in self.events.items() if not v.booked}
