from datetime import datetime, timedelta
import dateparser
import pytz
import re
from .calendar import check_time_slot_availability, find_available_slots, create_calendar_event, update_calendar_timezone, get_calendar_timezone, test_simple_event_creation

def parse_natural_time(user_input):
    """Enhanced time parsing for natural language"""
    try:
        user_input_lower = user_input.lower()
        
        tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz)
        
        print(f"🔍 Parsing input: '{user_input}'")
        print(f"🕐 Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        target_date = None
        
        if "tomorrow" in user_input_lower:
            target_date = now + timedelta(days=1)
            print(f"📅 Target date (tomorrow): {target_date.strftime('%Y-%m-%d')}")
        elif "today" in user_input_lower:
            target_date = now
            print(f"📅 Target date (today): {target_date.strftime('%Y-%m-%d')}")
        elif "next week" in user_input_lower:
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:  
                days_until_monday = 7
            target_date = now + timedelta(days=days_until_monday)
            print(f"📅 Target date (next week): {target_date.strftime('%Y-%m-%d')}")
        else:
            weekdays = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            for day_name, day_num in weekdays.items():
                if day_name in user_input_lower:
                    days_ahead = day_num - now.weekday()
                    if days_ahead <= 0:  
                        days_ahead += 7
                    
                    if "next" in user_input_lower:
                        days_ahead += 7
                    
                    target_date = now + timedelta(days=days_ahead)
                    print(f"📅 Target date ({day_name}): {target_date.strftime('%Y-%m-%d')}")
                    break
        
        between_pattern = re.search(r'between (\d+)[-–](\d+)\s*(am|pm)?', user_input_lower)
        if between_pattern:
            start_hour = int(between_pattern.group(1))
            end_hour = int(between_pattern.group(2))
            period = between_pattern.group(3)
            
            if period == 'pm' and start_hour != 12:
                start_hour += 12
            elif period == 'am' and start_hour == 12:
                start_hour = 0
            
            if target_date is None:
                target_date = now + timedelta(days=1)
                while target_date.weekday() >= 5:  
                    target_date += timedelta(days=1)
            
            naive_time = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0, tzinfo=None)
            result_time = tz.localize(naive_time)
            print(f"🕐 Parsed time (between pattern): {result_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return result_time
        
        time_range_patterns = [
            r'(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2})\s*(am|pm)',  
            r'(\d{1,2}):(\d{2})\s*(?:to|-|–)\s*(\d{1,2}):(\d{2})\s*(am|pm)?',  
        ]
        
        for pattern in time_range_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                if len(match.groups()) == 3:  
                    start_hour = int(match.group(1))
                    end_hour = int(match.group(2))
                    period = match.group(3)
                    
                    if period == 'pm' and start_hour != 12:
                        start_hour += 12
                    elif period == 'am' and start_hour == 12:
                        start_hour = 0
                    
                    if target_date is None:
                        target_date = now + timedelta(days=1)
                    
                    naive_time = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0, tzinfo=None)
                    result_time = tz.localize(naive_time)
                    print(f"🕐 Parsed time (range pattern): {result_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    return result_time
        
        time_patterns = [
            r'(\d{1,2})\s*(am|pm)', 
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',  
            r'(\d{1,2})\s*o\'?clock',  
        ]
        
        extracted_hour = None
        extracted_minute = 0
        is_pm = False
        
        for pattern in time_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                if len(match.groups()) >= 2 and match.group(2) in ['am', 'pm']:
                    extracted_hour = int(match.group(1))
                    is_pm = match.group(2) == 'pm'
                    print(f"⏰ Found time pattern: {extracted_hour} {match.group(2)}")
                elif len(match.groups()) >= 3 and match.group(3):
                    extracted_hour = int(match.group(1))
                    extracted_minute = int(match.group(2))
                    is_pm = match.group(3) == 'pm'
                    print(f"⏰ Found time pattern: {extracted_hour}:{extracted_minute} {match.group(3)}")
                elif len(match.groups()) >= 2:
                    extracted_hour = int(match.group(1))
                    if len(match.groups()) >= 2 and match.group(2).isdigit():
                        extracted_minute = int(match.group(2))
                    print(f"⏰ Found time pattern: {extracted_hour}:{extracted_minute}")
                else:
                    extracted_hour = int(match.group(1))
                    print(f"⏰ Found time pattern: {extracted_hour} o'clock")
                break
        
        if extracted_hour is not None:
            original_hour = extracted_hour
            if is_pm and extracted_hour != 12:
                extracted_hour += 12
            elif not is_pm and extracted_hour == 12:
                extracted_hour = 0
            
            if "evening" in user_input_lower or "night" in user_input_lower:
                if extracted_hour < 12 and not is_pm:
                    extracted_hour += 12
                    print(f"🌆 Evening/night context: adjusted to {extracted_hour}:00")
            
            print(f"🔢 Converted {original_hour}{'pm' if is_pm else 'am'} to 24-hour: {extracted_hour}:00")
        
        if target_date and extracted_hour is not None:
            naive_time = target_date.replace(
                hour=extracted_hour, 
                minute=extracted_minute, 
                second=0, 
                microsecond=0,
                tzinfo=None
            )
            result_time = tz.localize(naive_time)
            print(f"🎯 Final parsed time: {result_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return result_time
        
        if extracted_hour is not None:
            naive_time = now.replace(hour=extracted_hour, minute=extracted_minute, second=0, microsecond=0, tzinfo=None)
            target_time = tz.localize(naive_time)
            if target_time <= now:
                target_time += timedelta(days=1)
            print(f"🎯 Final parsed time: {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return target_time
        
        if target_date:
            if "afternoon" in user_input_lower:
                naive_time = target_date.replace(hour=14, minute=0, second=0, microsecond=0, tzinfo=None)
            elif "morning" in user_input_lower:
                naive_time = target_date.replace(hour=10, minute=0, second=0, microsecond=0, tzinfo=None)
            elif "evening" in user_input_lower or "night" in user_input_lower:
                naive_time = target_date.replace(hour=19, minute=0, second=0, microsecond=0, tzinfo=None)
            else:
                naive_time = target_date.replace(hour=10, minute=0, second=0, microsecond=0, tzinfo=None)
            
            result_time = tz.localize(naive_time)
            print(f"🎯 Final parsed time (relative): {result_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return result_time
        
        parsed_time = dateparser.parse(user_input, settings={'TIMEZONE': 'Asia/Kolkata'})
        if parsed_time:
            if parsed_time.tzinfo is None:
                parsed_time = tz.localize(parsed_time)
            print(f"🎯 Final parsed time (dateparser): {parsed_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return parsed_time
        
        print("❌ Could not parse time from input")
        return None
        
    except Exception as e:
        print(f"Error parsing time: {e}")
        return None

def parse_time_with_duration(user_input):
    """Parse time and extract duration information"""
    try:
        user_input_lower = user_input.lower()
        tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz)
        
        target_date = None
        
        if "tomorrow" in user_input_lower:
            target_date = now + timedelta(days=1)
        elif "today" in user_input_lower:
            target_date = now
        elif "next week" in user_input_lower:
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:  
                days_until_monday = 7
            target_date = now + timedelta(days=days_until_monday)
        else:
            weekdays = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            for day_name, day_num in weekdays.items():
                if day_name in user_input_lower:
                    days_ahead = day_num - now.weekday()
                    if days_ahead <= 0:  
                        days_ahead += 7
                    
                    if "next" in user_input_lower:
                        days_ahead += 7
                    
                    target_date = now + timedelta(days=days_ahead)
                    break
        
        between_pattern = re.search(r'between (\d+)[-–](\d+)\s*(am|pm)?', user_input_lower)
        if between_pattern:
            start_hour = int(between_pattern.group(1))
            end_hour = int(between_pattern.group(2))
            period = between_pattern.group(3)
            
            if period == 'pm' and start_hour != 12:
                start_hour += 12
                end_hour += 12
            elif period == 'am' and start_hour == 12:
                start_hour = 0
            elif period == 'am' and end_hour == 12:
                end_hour = 0
            
            if target_date is None:
                target_date = now + timedelta(days=1)
                while target_date.weekday() >= 5:  
                    target_date += timedelta(days=1)
            
            naive_time = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0, tzinfo=None)
            start_time = tz.localize(naive_time)
            
            duration_minutes = (end_hour - start_hour) * 60
            
            return {
                'start_time': start_time,
                'duration': duration_minutes,
                'is_range': True
            }
        
        time_range_patterns = [
            r'(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2})\s*(am|pm)',  # 10 to 11 am, 2-3 pm
            r'(\d{1,2}):(\d{2})\s*(?:to|-|–)\s*(\d{1,2}):(\d{2})\s*(am|pm)?',  # 10:30 to 11:30 am
        ]
        
        for pattern in time_range_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                if len(match.groups()) == 3:  # Format: 10 to 11 am
                    start_hour = int(match.group(1))
                    end_hour = int(match.group(2))
                    period = match.group(3)
                    
                    # Convert to 24-hour format
                    if period == 'pm' and start_hour != 12:
                        start_hour += 12
                        end_hour += 12
                    elif period == 'am' and start_hour == 12:
                        start_hour = 0
                    elif period == 'am' and end_hour == 12:
                        end_hour = 0
                    
                    # Use target_date if already determined, otherwise default to tomorrow
                    if target_date is None:
                        target_date = now + timedelta(days=1)
                    
                    # Create naive datetime first, then localize
                    naive_time = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0, tzinfo=None)
                    start_time = tz.localize(naive_time)
                    
                    duration_minutes = (end_hour - start_hour) * 60
                    
                    return {
                        'start_time': start_time,
                        'duration': duration_minutes,
                        'is_range': True
                    }
        
        # If no range found, use regular parsing
        parsed_time = parse_natural_time(user_input)
        if parsed_time and isinstance(parsed_time, datetime):
            return {
                'start_time': parsed_time,
                'duration': 30,  # Default 30 minutes
                'is_range': False
            }
        
        return None
        
    except Exception as e:
        print(f"Error parsing time with duration: {e}")
        return None

def check_availability(user_input, start_date=None, end_date=None):
    """Check availability and return available slots"""
    try:
        if start_date is None:
            start_date = datetime.now(pytz.timezone('Asia/Kolkata'))
        
        if end_date is None:
            end_date = start_date + timedelta(days=7)  # Check next 7 days
        
        available_slots = find_available_slots(start_date, end_date)
        return available_slots
    except Exception as e:
        print(f"Error checking availability: {e}")
        return []

def suggest_time_slots(user_input):
    """Suggest available time slots based on user input"""
    try:
        # First try to parse with duration
        time_info = parse_time_with_duration(user_input)
        
        if time_info and time_info.get('start_time'):
            start_time = time_info['start_time']
            duration = time_info.get('duration', 30)
            
            # Check if the specific time is available
            if check_time_slot_availability(start_time, duration):
                return [start_time]
            else:
                # Find nearby available slots
                start_search = start_time.replace(hour=9, minute=0)
                end_search = start_time.replace(hour=18, minute=0)
                return find_available_slots(start_search, end_search)
        else:
            # General availability check
            now = datetime.now(pytz.timezone('Asia/Kolkata'))
            return find_available_slots(now, now + timedelta(days=7))
    except Exception as e:
        print(f"Error suggesting time slots: {e}")
        return []

def book_appointment(user_input, selected_time, title="Meeting via AI Booking Agent"):
    """Book an appointment at the specified time"""
    try:
        if not isinstance(selected_time, datetime):
            return "❌ Invalid time format."
        
        # Ensure timezone awareness - convert to Asia/Kolkata if needed
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        if selected_time.tzinfo is None:
            selected_time = kolkata_tz.localize(selected_time)
        elif selected_time.tzinfo != kolkata_tz:
            selected_time = selected_time.astimezone(kolkata_tz)
        
        # Parse duration from user input
        time_info = parse_time_with_duration(user_input)
        duration_minutes = 30  # Default duration
        
        if time_info and time_info.get('duration'):
            duration_minutes = time_info['duration']
        
        if not check_time_slot_availability(selected_time, duration_minutes):
            return "❌ This time slot is no longer available."
        
        # Check and update calendar timezone first
        print("🔧 Checking calendar timezone...")
        current_tz = get_calendar_timezone()
        if current_tz != 'Asia/Kolkata':
            print("🔄 Updating calendar timezone...")
            update_calendar_timezone()
        
        print(f"📅 Booking appointment for: {selected_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Create the event
        event_link = create_calendar_event(title, user_input, selected_time, duration_minutes)
        
        if event_link:
            formatted_time = selected_time.strftime("%B %d, %Y at %I:%M %p")
            
            if duration_minutes > 30:
                end_time = selected_time + timedelta(minutes=duration_minutes)
                formatted_end_time = end_time.strftime("%I:%M %p")
                return f"✅ Appointment booked successfully for {formatted_time} to {formatted_end_time} (Asia/Kolkata timezone)!\n\n🔗 Event link: {event_link}\n\n"
            else:
                return f"✅ Appointment booked successfully for {formatted_time} (Asia/Kolkata timezone)!\n\n🔗 Event link: {event_link}\n\n"
        else:
            return "❌ Failed to create the appointment. Please try again."
    except Exception as e:
        print(f"Error booking appointment: {e}")
        return "❌ Failed to create the appointment. Please try again."

def format_time_slots(slots):
    """Format time slots for display"""
    try:
        if not slots:
            return "No available slots found."
        
        formatted_slots = []
        for i, slot in enumerate(slots[:5], 1):  # Show first 5 slots
            formatted_time = slot.strftime("%A, %B %d at %I:%M %p")
            formatted_slots.append(f"{i}. {formatted_time}")
        
        return "\n".join(formatted_slots)
    except Exception as e:
        print(f"Error formatting time slots: {e}")
        return "Error formatting available times."

def debug_time_parsing(user_input):
    """Debug function to test time parsing"""
    print(f"\n🔍 DEBUG: Testing time parsing for '{user_input}'")
    result = parse_natural_time(user_input)
    if result:
        print(f"✅ Successfully parsed: {result.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print("❌ Failed to parse time")
    return result

def create_test_event():
    """Create a test event to verify timezone handling"""
    return test_simple_event_creation()


