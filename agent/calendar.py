from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle
import os
from datetime import datetime, timedelta
import pytz

def authenticate_google():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_calendar_events(start_time, end_time):
    """Get existing events in the specified time range"""
    try:
        service = authenticate_google()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return []

def check_time_slot_availability(start_time, duration_minutes=30):
    """Check if a specific time slot is available"""
    try:
        end_time = start_time + timedelta(minutes=duration_minutes)
        existing_events = get_calendar_events(start_time, end_time)
        
        for event in existing_events:
            if 'dateTime' in event['start']:
                event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            else:
                event_start = datetime.fromisoformat(event['start']['date'])
                
            if 'dateTime' in event['end']:
                event_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
            else:
                event_end = datetime.fromisoformat(event['end']['date'])
            
            if event_start.tzinfo is None:
                event_start = pytz.timezone('Asia/Kolkata').localize(event_start)
            if event_end.tzinfo is None:
                event_end = pytz.timezone('Asia/Kolkata').localize(event_end)
            
            if (start_time < event_end and end_time > event_start):
                return False
        
        return True
    except Exception as e:
        print(f"Error checking availability: {e}")
        return False

def find_available_slots(start_date, end_date, duration_minutes=30):
    """Find available time slots within a date range"""
    available_slots = []
    
    working_start = 9
    working_end = 18
    
    current_date = start_date.date()
    end_date_only = end_date.date()
    
    while current_date <= end_date_only:
        if current_date.weekday() < 5: 
            for hour in range(working_start, working_end):
                slot_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                slot_time = pytz.timezone('Asia/Kolkata').localize(slot_time)
                
                if slot_time > datetime.now(pytz.timezone('Asia/Kolkata')):
                    if check_time_slot_availability(slot_time, duration_minutes):
                        available_slots.append(slot_time)
                
                slot_time_30 = slot_time + timedelta(minutes=30)
                if slot_time_30.hour < working_end:
                    if check_time_slot_availability(slot_time_30, duration_minutes):
                        available_slots.append(slot_time_30)
        
        current_date += timedelta(days=1)
    
    return available_slots[:10]  

def create_calendar_event(title, description, start_time, duration_minutes=30):
    """Create a new calendar event using simple datetime format"""
    try:
        service = authenticate_google()
        
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        if start_time.tzinfo is None:
            start_time = kolkata_tz.localize(start_time)
        elif start_time.tzinfo != kolkata_tz:
            start_time = start_time.astimezone(kolkata_tz)
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        start_datetime_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
        end_datetime_str = end_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        print(f"🕐 Original request time: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📤 Sending to Google API (no timezone conversion): {start_datetime_str}")
        print(f"🌍 Timezone field: Asia/Kolkata")
        
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_datetime_str,
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': end_datetime_str,
                'timeZone': 'Asia/Kolkata'
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60}, 
                    {'method': 'popup', 'minutes': 10},       
                ],
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        event_link = created_event.get('htmlLink')
        
        print(f"✅ Created event: {created_event.get('summary')}")
        print(f"📅 API Response start time: {created_event.get('start')}")
        print(f"📅 API Response end time: {created_event.get('end')}")
        print(f"🔗 Event link: {event_link}")
        
        return event_link
        
    except Exception as e:
        print(f"❌ Error creating event: {e}")
        return None

def get_calendar_timezone():
    """Get the primary calendar's timezone"""
    try:
        service = authenticate_google()
        calendar = service.calendars().get(calendarId='primary').execute()
        current_tz = calendar.get('timeZone', 'Asia/Kolkata')
        print(f"📍 Current calendar timezone: {current_tz}")
        return current_tz
    except Exception as e:
        print(f"Error getting calendar timezone: {e}")
        return 'Asia/Kolkata'

def update_calendar_timezone():
    """Update the primary calendar timezone to Asia/Kolkata"""
    try:
        service = authenticate_google()
        
        calendar = service.calendars().get(calendarId='primary').execute()
        current_tz = calendar.get('timeZone')
        
        if current_tz != 'Asia/Kolkata':
            calendar['timeZone'] = 'Asia/Kolkata'
            
            updated_calendar = service.calendars().update(calendarId='primary', body=calendar).execute()
            
            print(f"🔄 Calendar timezone updated from {current_tz} to: {updated_calendar.get('timeZone')}")
            return updated_calendar.get('timeZone')
        else:
            print(f"✅ Calendar timezone already set to: {current_tz}")
            return current_tz
        
    except Exception as e:
        print(f"❌ Error updating calendar timezone: {e}")
        return None

def test_simple_event_creation():
    """Test function to create a simple event for debugging"""
    try:
        service = authenticate_google()
        
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        tomorrow = now + timedelta(days=1)
        test_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        event = {
            'summary': 'Test Event - 2 PM',
            'description': 'Testing timezone handling',
            'start': {
                'dateTime': '2025-06-29T14:00:00',
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': '2025-06-29T14:30:00',
                'timeZone': 'Asia/Kolkata'
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"🧪 Test event created: {created_event.get('htmlLink')}")
        print(f"🧪 Should show 2:00 PM - 2:30 PM on June 29")
        
        return created_event.get('htmlLink')
        
    except Exception as e:
        print(f"❌ Error creating test event: {e}")
        return None
