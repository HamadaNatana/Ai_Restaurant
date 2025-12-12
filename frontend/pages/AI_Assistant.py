import streamlit as st
import requests
from utils.auth_helper import require_role
from utils.sidebar import generate_sidebar

# 1. SETUP
st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")
generate_sidebar()
require_role(["VISITOR", "CUSTOMER", "VIP"])

# 2. CONFIGURATION
BASE_URL = "http://127.0.0.1:8000"
API_URLS = {
    "ask": f"{BASE_URL}/ai_assist/chat/ask/",
    "rate": f"{BASE_URL}/ai_assist/chat/rate/"
}

# 3. HELPER: RENDER SOURCE BADGE
def render_source_badge(source_type):
    if source_type == "kb":
        st.markdown(
            """
            <span style='background-color: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600;'>
            ✅ Verified Knowledge Base
            </span>
            """, 
            unsafe_allow_html=True
        )
    elif source_type == "llm":
        st.markdown(
            """
            <span style='background-color: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600;'>
            🧠 AI Generated (Mistral)
            </span>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.caption("Source: Unknown")

# 4. UI LAYOUT
st.title("🤖 AI Concierge")
st.caption("Ask about our menu, policies, or delivery options.")

# Initialize Session
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_ai_answer" not in st.session_state:
    st.session_state.last_ai_answer = None

col_chat, col_info = st.columns([2, 1])

# ==========================================
# LEFT COLUMN: CHAT INTERFACE
# ==========================================
with col_chat:
    # 1. Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"]) # Markdown handles bold/lists better than write
            
            # Show Source Badge for Assistant messages
            if msg["role"] == "assistant" and "source" in msg:
                render_source_badge(msg["source"])

    # 2. Handle New Input
    if prompt := st.chat_input("How can I help you today?"):
        # Show User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Generate AI Response
        with st.chat_message("assistant"):
            with st.spinner("Consulting the kitchen..."):
                try:
                    current_user = st.session_state.get("username")
                    payload = {
                        "customer_id": current_user if current_user else "1",
                        "question": prompt
                    }

                    # Call API
                    response = requests.post(API_URLS['ask'], json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        answer_data = data.get('answer', {})
                        
                        response_text = answer_data.get('answer', "I have no answer.")
                        source = answer_data.get('source', 'llm') # Default to llm if missing
                        ai_answer_id = answer_data.get('id')
                        
                        # Display Text
                        st.markdown(response_text)
                        
                        # Display Badge
                        render_source_badge(source)
                        
                        # Save to History
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response_text, 
                            "source": source
                        })
                        
                        # Save for Rating Panel
                        st.session_state.last_ai_answer = {
                            "id": ai_answer_id,
                            "source": source
                        }
                    
                    else:
                        st.error("I'm having trouble connecting right now.")
                        # Only show detailed error if you are debugging
                        # st.code(response.text)
                        
                except Exception as e:
                    st.error(f"Connection Error: {e}")

# ==========================================
# RIGHT COLUMN: RATINGS (UC21)
# ==========================================
with col_info:
    st.subheader("📝 Feedback")
    
    last_ans = st.session_state.last_ai_answer
    
    if last_ans:
        with st.container(border=True):
            st.write("**Rate the last response:**")
            
            # Context indicator
            if last_ans['source'] == 'kb':
                st.caption("You are rating a **Human-Verified** answer.")
            else:
                st.caption("You are rating an **AI-Generated** answer.")
            
            rating = st.slider("Stars", 0, 5, 5)
            
            if st.button("Submit Rating", use_container_width=True):
                try:
                    current_user = st.session_state.get("username")
                    if not current_user:
                        st.warning("Please log in to rate.")
                    else:
                        payload = {
                            "customer_id": current_user,
                            "ai_answer_id": last_ans['id'],
                            "stars": rating
                        }
                        res = requests.post(API_URLS['rate'], json=payload)
                        
                        if res.status_code == 200:
                            msg = res.json().get('message', '')
                            if "flagged" in msg.lower():
                                st.error("🚨 Response Flagged for Review")
                            else:
                                st.success("✅ Rating Received")
                        else:
                            st.error("Could not save rating.")
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("Start chatting to leave feedback.")

    st.divider()
    with st.expander("System Health"):
        st.write("🟢 **Frontend:** Online")
        st.write("🟢 **API:** Connected")
        st.write("🟢 **Ollama:** Active")