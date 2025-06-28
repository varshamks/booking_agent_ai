# import streamlit as st
# from agent.langgraph_agent import app

# st.set_page_config(page_title="AI Booking Agent", page_icon="🧠", layout="centered")
# st.title("🤖 AI Booking Agent with LangGraph")

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# for msg in st.session_state.messages:
#     st.chat_message(msg["role"]).write(msg["content"])

# user_input = st.chat_input("How can I help you book today?")

# if user_input:
#     st.session_state.messages.append({"role": "user", "content": user_input})
#     response = app.invoke({"user_input": user_input})
#     st.session_state.messages.append({"role": "assistant", "content": response["message"]})
#     st.chat_message("assistant").write(response["message"])



# import streamlit as st
# from agent.langgraph_agent import app

# st.set_page_config(page_title="🧑‍💼 AI Booking Assistant", layout="wide")
# st.title("📆 AI Calendar Booking Assistant")

# if "messages" not in st.session_state:
#     st.session_state["messages"] = []

# for msg in st.session_state["messages"]:
#     st.chat_message(msg["role"]).markdown(msg["content"])

# prompt = st.chat_input("Ask me to book a calendar event!")

# if prompt:
#     st.session_state["messages"].append({"role": "user", "content": prompt})
#     st.chat_message("user").markdown(prompt)

#     result = app(prompt)

#     st.session_state["messages"].append({"role": "assistant", "content": result})
#     st.chat_message("assistant").markdown(result)





import streamlit as st
from agent.langgraph_agent import app

st.set_page_config(page_title="🧑‍💼 AI Booking Assistant", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        margin-bottom: 2rem;
    }
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    .example-queries {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📆 AI Calendar Booking Assistant</h1>', unsafe_allow_html=True)

# Example queries section
with st.expander("💡 Example queries you can try:", expanded=False):
    st.markdown("""
    - "Hey, I want to schedule a call for tomorrow afternoon."
    - "Do you have any free time this Friday?"
    - "Book a meeting between 3-5 PM next week."
    - "I need to schedule an appointment for next Monday morning."
    - "What times are available this week?"
    """)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello! I'm your AI booking assistant. I can help you schedule appointments on your Google Calendar. What would you like to schedule today?"}
    ]

# Display chat messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask me to book a calendar event or check availability!"):
    # Add user message to chat history
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = app(prompt)
                st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state["messages"].append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}. Please try again."
                st.markdown(error_msg)
                st.session_state["messages"].append({"role": "assistant", "content": error_msg})

# Sidebar with additional information
with st.sidebar:
    st.markdown("### 🔧 Features")
    st.markdown("""
    - Natural language booking
    - Calendar availability checking
    - Smart time slot suggestions
    - Google Calendar integration
    - Conversational interface
    """)
    
    st.markdown("### 📝 Instructions")
    st.markdown("""
    1. Make sure you have set up your Google Calendar credentials
    2. Ask to book an appointment in natural language
    3. Follow the conversation flow to confirm your booking
    """)
    
    if st.button("🔄 Clear Chat History"):
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hello! I'm your AI booking assistant. I can help you schedule appointments on your Google Calendar. What would you like to schedule today?"}
        ]
        st.rerun()
