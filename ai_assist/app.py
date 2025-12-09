import streamlit as st

def main():
    st.set_page_config(
        page_title="AI Restaurant – Home",
        page_icon="🍽️",
        layout="wide",
    )

    st.markdown(
        """
        <div style="background-color:#111827;padding:12px 18px;border-radius:0 0 10px 10px;">
            <h2 style="color:white;margin:0;">AI-Enabled Online Restaurant Order & Delivery System</h2>
            <p style="color:#9ca3af;margin:4px 0 0 0;font-size:13px;">
                Home Dashboard – jump to any feature (UC16, UC20–UC22)
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Simple "login" simulation for your part of the project
    st.sidebar.header("User Info (demo)")
    username = st.sidebar.text_input("Username", value="demo_customer")
    role = st.sidebar.selectbox(
        "Role",
        options=["CUSTOMER", "VIP", "MANAGER"],
        index=0,
        help="This just simulates roles for your features.",
    )

    # Save into session so all pages share it
    if "username" not in st.session_state:
        st.session_state.username = username
    if "role" not in st.session_state:
        st.session_state.role = role

    st.session_state.username = username
    st.session_state.role = role

    st.write("")
    st.write("### Welcome, ", f"**{username}**  _(role: {role})_")

    st.write(
        """
        This home dashboard is just for navigation.  
        Use the buttons below or the sidebar **Pages** section to open features:
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.page_link(
            "pages/1_AI_Chat.py",
            label="🤖 AI Customer Service Chat (UC20–21)",
            icon="🤖",
        )

    with col2:
        st.page_link(
            "pages/2_Discussion_Board.py",
            label="💬 Discussion Board (UC16)",
            icon="💬",
        )

    with col3:
        st.page_link(
            "pages/3_Allergy_Settings.py",
            label="⚕️ Allergy Settings (UC22)",
            icon="⚕️",
        )

    st.markdown("---")
    st.caption(
        "Your part of the project: AI Customer Service Chat, Discussion Board, and Allergy Filtering."
    )

if __name__ == "__main__":
    main()
