import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from agent.logic import parse_natural_time, suggest_time_slots, book_appointment, format_time_slots, parse_time_with_duration
import re
from datetime import datetime, timedelta
import pytz

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ['OPENAI_API_KEY'] = openai_api_key

llm = ChatOpenAI(api_key=openai_api_key, temperature=0.7)

conversation_state = {
    'stage': 'initial',  
    'suggested_slots': [],
    'selected_time': None,
    'user_intent': None,
    'last_requested_time': None,
    'current_user_input': None  
}

def reset_conversation_state():
    """Reset conversation state"""
    global conversation_state
    conversation_state = {
        'stage': 'initial',
        'suggested_slots': [],
        'selected_time': None,
        'user_intent': None,
        'last_requested_time': None,
        'current_user_input': None
    }

def detect_intent(user_input):
    """Detect user intent from input"""
    user_input_lower = user_input.lower()
    
    booking_keywords = ['book', 'schedule', 'appointment', 'meeting', 'call', 'reserve']
    availability_keywords = ['available', 'free', 'time', 'when', 'slot']
    confirmation_keywords = ['yes', 'confirm', 'ok', 'sure', 'book it', 'that works']
    
    if any(keyword in user_input_lower for keyword in booking_keywords):
        return 'booking'
    elif any(keyword in user_input_lower for keyword in availability_keywords):
        return 'availability'
    elif any(keyword in user_input_lower for keyword in confirmation_keywords):
        return 'confirmation'
    elif re.search(r'\b\d+\b', user_input):  
        return 'slot_selection'
    else:
        return 'general'

def handle_booking_intent(user_input):
    """Handle booking-related requests"""
    global conversation_state
    
    try:
        conversation_state['current_user_input'] = user_input
        
        time_info = parse_time_with_duration(user_input)
        
        if time_info and time_info.get('start_time'):
            start_time = time_info['start_time']
            duration = time_info.get('duration', 30)
            is_range = time_info.get('is_range', False)
            
            suggested_slots = suggest_time_slots(user_input)
            
            if suggested_slots and start_time in suggested_slots:
                conversation_state['selected_time'] = start_time
                conversation_state['stage'] = 'booking_confirmation'
                
                if is_range and duration > 30:
                    end_time = start_time + timedelta(minutes=duration)
                    formatted_time = start_time.strftime("%A, %B %d at %I:%M %p")
                    formatted_end_time = end_time.strftime("%I:%M %p")
                    return f"Great! I found that {formatted_time} to {formatted_end_time} is available. Would you like me to book this appointment for you?"
                else:
                    formatted_time = start_time.strftime("%A, %B %d at %I:%M %p")
                    return f"Great! I found that {formatted_time} is available. Would you like me to book this appointment for you?"
            elif suggested_slots:
                conversation_state['suggested_slots'] = suggested_slots
                conversation_state['stage'] = 'availability_check'
                slots_text = format_time_slots(suggested_slots)
                
                if is_range and duration > 30:
                    duration_hours = duration // 60
                    return f"The exact {duration_hours}-hour time slot you requested isn't available, but I found these alternatives:\n\n{slots_text}\n\nWhich slot would you prefer? Just reply with the number."
                else:
                    return f"The exact time you requested isn't available, but I found these alternatives:\n\n{slots_text}\n\nWhich slot would you prefer? Just reply with the number."
            else:
                return "I couldn't find any available slots for that time. Could you try a different time or date?"
        else:
            suggested_slots = suggest_time_slots(user_input)
            if suggested_slots:
                conversation_state['suggested_slots'] = suggested_slots
                conversation_state['stage'] = 'availability_check'
                slots_text = format_time_slots(suggested_slots)
                return f"I'd be happy to help you schedule an appointment! Here are some available time slots:\n\n{slots_text}\n\nWhich slot works best for you? Just reply with the number."
            else:
                return "I couldn't find any available slots. Please try a different time range."
                
    except Exception as e:
        print(f"Error in handle_booking_intent: {e}")
        return "I had trouble understanding your time request. Could you please rephrase it? For example: 'Book a meeting tomorrow at 3 PM' or 'Schedule a call between 2-4 PM next week'."

def handle_availability_intent(user_input):
    """Handle availability check requests"""
    global conversation_state
    
    try:
        suggested_slots = suggest_time_slots(user_input)
        
        if suggested_slots:
            conversation_state['suggested_slots'] = suggested_slots
            conversation_state['stage'] = 'availability_check'
            slots_text = format_time_slots(suggested_slots)
            return f"Here are the available time slots:\n\n{slots_text}\n\nWould you like to book any of these? Just reply with the number."
        else:
            return "I don't have any available slots for that time period. Could you try a different time or date?"
    except Exception as e:
        print(f"Error in handle_availability_intent: {e}")
        return "I had trouble checking availability. Could you please try again?"

def handle_slot_selection(user_input):
    """Handle slot selection by number"""
    global conversation_state
    
    try:
        slot_number = int(re.search(r'\b(\d+)\b', user_input).group(1))
        
        if 1 <= slot_number <= len(conversation_state['suggested_slots']):
            selected_slot = conversation_state['suggested_slots'][slot_number - 1]
            conversation_state['selected_time'] = selected_slot
            conversation_state['stage'] = 'booking_confirmation'
            formatted_time = selected_slot.strftime("%A, %B %d at %I:%M %p")
            return f"Perfect! You've selected {formatted_time}. Shall I go ahead and book this appointment for you?"
        else:
            return f"Please select a number between 1 and {len(conversation_state['suggested_slots'])}."
    except Exception as e:
        print(f"Error in handle_slot_selection: {e}")
        return "I didn't understand which slot you'd like. Please reply with the number of your preferred time slot."

def handle_confirmation(user_input):
    """Handle booking confirmation"""
    global conversation_state
    
    try:
        if conversation_state['selected_time']:
            original_input = conversation_state.get('current_user_input', user_input)
            result = book_appointment(original_input, conversation_state['selected_time'])
            conversation_state['stage'] = 'booking_complete'
            reset_conversation_state()  
            return result
        else:
            return "I don't have a time slot selected. Please choose a time slot first."
    except Exception as e:
        print(f"Error in handle_confirmation: {e}")
        return "I encountered an error while booking. Please try again."

def app(user_input):
    """Main application logic with conversation flow"""
    global conversation_state
    
    print(f"🖋️ User input received: {user_input}")
    print(f"📊 Current stage: {conversation_state['stage']}")
    
    try:
        user_intent = detect_intent(user_input)
        print(f"🎯 Detected intent: {user_intent}")
        
        if any(phrase in user_input.lower() for phrase in ['why not', 'why can\'t', 'what about']):
            if conversation_state.get('last_requested_time'):
                return f"The specific time you requested might be outside business hours (9 AM - 6 PM on weekdays) or may conflict with an existing appointment. Let me check for the exact time you want - could you specify the exact time again?"
            else:
                return "Let me help you find the exact time you're looking for. Could you please specify the exact time you'd prefer?"
        
        if conversation_state['stage'] == 'initial':
            if user_intent == 'booking':
                try:
                    parsed_time = parse_natural_time(user_input)
                    if parsed_time:
                        conversation_state['last_requested_time'] = parsed_time
                except:
                    pass  
                return handle_booking_intent(user_input)
            elif user_intent == 'availability':
                return handle_availability_intent(user_input)
            else:
                response = llm([
                    SystemMessage(content="""You are a helpful AI booking assistant. Your main job is to help users book appointments on their Google Calendar. 
                    
                    When users ask about booking, scheduling, or availability, guide them through the process. 
                    For general questions, be helpful but try to steer the conversation toward how you can help them with scheduling.
                    
                    Keep responses concise and friendly."""),
                    HumanMessage(content=user_input)
                ]).content
                
                return response + "\n\nI can help you book appointments on your calendar. Just let me know when you'd like to schedule something!"
        
        elif conversation_state['stage'] == 'availability_check':
            if user_intent == 'slot_selection':
                return handle_slot_selection(user_input)
            elif user_intent == 'booking' or user_intent == 'confirmation':
                if re.search(r'\b\d+\b', user_input):
                    return handle_slot_selection(user_input)
                else:
                    return "Which time slot would you like to book? Please reply with the number of your preferred slot."
            else:
                return "Which time slot would you like to book? Please reply with the number (1, 2, 3, etc.) of your preferred time."
        
        elif conversation_state['stage'] == 'booking_confirmation':
            if user_intent == 'confirmation' or 'yes' in user_input.lower() or 'confirm' in user_input.lower():
                return handle_confirmation(user_input)
            elif 'no' in user_input.lower() or 'cancel' in user_input.lower():
                reset_conversation_state()
                return "No problem! Let me know if you'd like to schedule a different time."
            else:
                return "Should I go ahead and book this appointment? Please reply with 'yes' to confirm or 'no' to cancel."
        
        else:
            # Reset state and handle as new conversation
            reset_conversation_state()
            return app(user_input)
            
    except Exception as e:
        print(f"Error in app function: {e}")
        # Reset state on error and provide helpful message
        reset_conversation_state()
        return f"I encountered an error processing your request. Let me help you start fresh - what would you like to schedule? You can try phrases like 'Book a meeting tomorrow at 3 PM' or 'Schedule a call between 2-4 PM next week'."
