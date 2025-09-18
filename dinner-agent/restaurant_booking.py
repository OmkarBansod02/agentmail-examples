import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv

from stagehand import Stagehand, StagehandConfig

load_dotenv()


class RestaurantBooking:
    """Handles OpenTable reservation booking using Stagehand"""
    
    def __init__(self):
        self.stagehand = None
        self.config = StagehandConfig(
            env="BROWSERBASE",
            api_key=os.getenv("BROWSERBASE_API_KEY"),
            project_id=os.getenv("BROWSERBASE_PROJECT_ID"),
            model_name="gpt-4o",
            model_client_options={"apiKey": os.getenv("OPENAI_API_KEY")}
        )
    
    async def init_browser(self):
        """Initialize the Stagehand browser session"""
        try:
            self.stagehand = Stagehand(
                config=self.config,
                server_url=os.getenv("STAGEHAND_API_URL")
            )
            await self.stagehand.init()
            print(f"Browser session created: {self.stagehand.session_id}")
            return True
        except Exception as e:
            print(f"Error initializing browser: {e}")
            return False
    
    async def close_browser(self):
        """Close the browser session"""
        if self.stagehand:
            await self.stagehand.close()
    
    async def book_opentable_reservation(self, restaurant_info: Dict, party_size: int,
                                       date: str, time: str, organizer_name: str,
                                       organizer_email: str) -> Dict:
        """
        Book a reservation on OpenTable
        Returns booking confirmation details
        """
        if not await self.init_browser():
            return {"success": False, "error": "Failed to initialize browser"}
        
        try:
            page = self.stagehand.page
            
            # Navigate to OpenTable
            await page.goto("https://www.opentable.com")
            await asyncio.sleep(2)
            
            # Search for the restaurant
            restaurant_name = restaurant_info.get("name", "")
            
            # Use the search functionality
            await page.act(f"search for {restaurant_name}")
            await asyncio.sleep(3)
            
            # Click on the restaurant from search results
            await page.act(f"click on {restaurant_name} in the search results")
            await asyncio.sleep(3)
            
            # Look for reservation booking section
            await page.act("find the reservation booking section")
            await asyncio.sleep(2)
            
            # Set party size
            await page.act(f"set party size to {party_size} people")
            await asyncio.sleep(1)
            
            # Set date - convert date string to proper format
            formatted_date = self._format_date_for_opentable(date)
            await page.act(f"select date {formatted_date}")
            await asyncio.sleep(1)
            
            # Set time
            formatted_time = self._format_time_for_opentable(time)
            await page.act(f"select time {formatted_time}")
            await asyncio.sleep(1)
            
            # Click find table or search button
            await page.act("click find table or search for available times")
            await asyncio.sleep(5)
            
            # Select the first available time slot
            await page.act("select the first available time slot")
            await asyncio.sleep(3)
            
            # Fill in reservation details
            await page.act(f"enter name as {organizer_name}")
            await asyncio.sleep(1)
            
            await page.act(f"enter email as {organizer_email}")
            await asyncio.sleep(1)
            
            # Submit the reservation
            await page.act("submit the reservation or complete booking")
            await asyncio.sleep(5)
            
            # Extract confirmation details
            confirmation_data = await page.extract(
                instruction="extract reservation confirmation details including confirmation number, restaurant name, date, time, and any confirmation URL",
                schema={
                    "confirmation_number": "string",
                    "restaurant_name": "string", 
                    "date": "string",
                    "time": "string",
                    "confirmation_url": "string",
                    "party_size": "number"
                }
            )
            
            # Take a screenshot for confirmation
            screenshot_path = f"booking_confirmation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            
            await self.close_browser()
            
            return {
                "success": True,
                "confirmation_number": confirmation_data.get("confirmation_number", "N/A"),
                "restaurant_name": confirmation_data.get("restaurant_name", restaurant_name),
                "date": confirmation_data.get("date", date),
                "time": confirmation_data.get("time", time),
                "party_size": confirmation_data.get("party_size", party_size),
                "confirmation_url": confirmation_data.get("confirmation_url", ""),
                "screenshot_path": screenshot_path
            }
            
        except Exception as e:
            print(f"Error during booking: {e}")
            await self.close_browser()
            return {
                "success": False,
                "error": str(e),
                "restaurant_name": restaurant_info.get("name", "Unknown")
            }
    
    def _format_date_for_opentable(self, date_str: str) -> str:
        """Format date string for OpenTable (e.g., 'Saturday' -> specific date)"""
        try:
            # Handle day names like "Saturday", "Sunday", etc.
            days = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            date_lower = date_str.lower()
            if date_lower in days:
                # Find the next occurrence of this day
                today = datetime.now()
                days_ahead = days[date_lower] - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                return target_date.strftime("%B %d, %Y")  # e.g., "January 20, 2024"
            
            # If it's already a specific date, return as is
            return date_str
            
        except Exception:
            # Fallback to tomorrow
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow.strftime("%B %d, %Y")
    
    def _format_time_for_opentable(self, time_str: str) -> str:
        """Format time string for OpenTable"""
        try:
            # Handle various time formats
            time_str = time_str.strip().lower()
            
            # Convert common formats
            if 'pm' in time_str or 'am' in time_str:
                return time_str
            
            # Handle 24-hour format
            if ':' in time_str and len(time_str.split(':')[0]) <= 2:
                hour, minute = time_str.split(':')
                hour = int(hour)
                if hour >= 12:
                    if hour > 12:
                        hour -= 12
                    return f"{hour}:{minute} PM"
                else:
                    if hour == 0:
                        hour = 12
                    return f"{hour}:{minute} AM"
            
            # Default fallback
            return "7:00 PM"
            
        except Exception:
            return "7:00 PM"
    
    async def verify_booking(self, confirmation_url: str) -> bool:
        """Verify booking by checking confirmation URL"""
        if not confirmation_url:
            return False
        
        try:
            if not await self.init_browser():
                return False
            
            page = self.stagehand.page
            await page.goto(confirmation_url)
            await asyncio.sleep(3)
            
            # Check if the page contains confirmation details
            booking_status = await page.extract(
                instruction="check if this page shows a confirmed reservation",
                schema={"is_confirmed": "boolean", "status": "string"}
            )
            
            await self.close_browser()
            return booking_status.get("is_confirmed", False)
            
        except Exception as e:
            print(f"Error verifying booking: {e}")
            if self.stagehand:
                await self.close_browser()
            return False
