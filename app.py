import streamlit as st
from groq import Groq
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Streamlit Chat", page_icon="💬")
st.title("Interview Simulator Chatbot")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True
def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:
        
    st.subheader('Personal Information', divider='rainbow')
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["name"] = st.text_input(label='Name', max_chars=40, value=st.session_state["name"], placeholder="Enter Your Name")
    st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], height=None, max_chars=200, placeholder="Describe Your Experience")
    st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], height=None, max_chars=200, placeholder="List Your Skills")

    st.subheader(' Target Company And Position', divider='rainbow')
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"
        
    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose Level",
            key="visibility",
            options=["Junior", "Mid-Level", "Senior"],
        )
    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a Position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "AI Engineer", "Financial Analyst")
        )
    st.session_state["company"] = st.selectbox(
        "Choose a Company",
        ("Google", "Microsoft", "IBM", "Fractal Analytics", "JPMorgan Chase",
        "Amazon", "Adobe", "Datadog", "Infosys", "Wipro",
        "Meta", "OpenAI", "NVIDIA", "Accenture", "Capgemini",
        "Tableau", "Salesforce", "Deloitte", "KPMG", "PwC",
        "Anthropic", "Hugging Face", "Cisco", "Honeywell", "Shell",
        "Goldman Sachs", "Morgan Stanley", "Barclays", "Citigroup", "HSBC")
    )
    st.write(f"**Your Information**: {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}")

    if st.button("Start Interview", on_click=complete_setup):
         st.write("Setup Complete. Starting Interview....")

if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        """
Start by introducing yourself
""",
        icon="spinner"
    )

    client = Groq(api_key=st.secrets["api_key"])

    if "groq_model" not in st.session_state:
        st.session_state["groq_model"] = "qwen/qwen3.6-27b"

    if not st.session_state.messages:
        st.session_state.messages = [
             {
                 "role": "system",
                 "content": (
                     f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                     f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                     f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                     f"at the company {st.session_state['company']}. "
                     "CRITICAL RULE: Always ask **only one question at a time**. "
                     "Wait for the candidate's response before asking the next question. "
                     "Do not list multiple questions in a single message."
                 )
             }
        ]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer.", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    current_messages = list(st.session_state.messages)
                    # If this is the 5th user message, instruct the system to wrap up
                    if st.session_state.user_message_count == 4:
                        current_messages.append({
                            "role": "system", 
                            "content": "The interview is now over. Write a final closing message saying: 'Thank you for the interview! Click below to get your feedback.'"
                        })

                    stream = client.chat.completions.create(
                        model=st.session_state["groq_model"],
                        messages=[{
                            "role": m["role"], "content": m["content"]
                        } for m in current_messages],
                        stream=True,
                        reasoning_format="hidden"
                    )
                    
                    def clean_stream(api_stream):
                        for chunk in api_stream:
                            if chunk.choices and chunk.choices[0].delta.content:
                                yield chunk.choices[0].delta.content

                    response = st.write_stream(clean_stream(stream))
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    if "429" in str(e) or "rate_limit" in str(e).lower():
                        st.error("Too many requests! Please try again after some time.")
                    else:
                        st.error(f"An error occurred: {e}")

            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
         st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get FeedBack...", on_click=show_feedback):
        st.write("fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
    feedback_client = Groq(api_key=st.secrets["api_key"])

    try:
        feedback_completion = feedback_client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
                Start your response with a polite opening line: "Thank you so much! Here is your feedback:"
                Before the Feedback give a score of 1 to 10.
                Follow this format:
                Thank you so much! Here is your feedback:
                Overal Score: //Your score
                Feedback: //Here you put your feedback
                Give only the feedback do not ask any additional questions.
                """},
                {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any conversation: {conversation_history}"}
            ],
            reasoning_format="hidden",
        )
        st.write(feedback_completion.choices[0].message.content)
    except Exception as e:
        if "429" in str(e) or "rate_limit" in str(e).lower():
            st.error("Too many requests while generating feedback! Please try again after some time.")
        else:
            st.error(f"An error occurred: {e}")

    if st.button("Restart Interview", type="primary"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")
