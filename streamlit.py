
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import random
import streamlit.components.v1 as components


# ---------------------------
# Database Initialization
# ---------------------------
def init_db():
    conn = sqlite3.connect("goldenage.db")
    cursor = conn.cursor()
    # Medication Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medication (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine TEXT,
        time TEXT,
        taken INTEGER DEFAULT 0
    )
    """)
    # Scores Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        user TEXT PRIMARY KEY,
        score INTEGER DEFAULT 0
    )
    """)
    # Virtual Pet Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pet (
        user TEXT PRIMARY KEY,
        food INTEGER DEFAULT 0,
        mood TEXT DEFAULT 'happy'
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# Page Navigation (Sidebar)
# ---------------------------
page = st.sidebar.radio("Select Page", ["Chatbot", "Medication & Virtual Pet", "Arithmetic Game"])

# ---------------------------
# Chatbot Page (Only Voiceflow)
# ---------------------------
if page == "Chatbot":
    st.title("GoldenAge Buddy Chatbot")
    st.subheader('Click the widget below to chat with the chatbot')

    components.html("""
        <script type="text/javascript">
            (function(d, t) {
                var v = d.createElement(t), s = d.getElementsByTagName(t)[0];
                v.onload = function() {
                    window.voiceflow.chat.load({
                    verify: { projectID: '67b0d617aa5f0f510e625181' },
                    url: 'https://general-runtime.voiceflow.com',
                    versionID: 'production'
                    });
                }
                v.src = "https://cdn.voiceflow.com/widget-next/bundle.mjs"; v.type = "text/javascript"; s.parentNode.insertBefore(v, s);
            })(document, 'script');
        </script>
        """, height=600)
    
# ---------------------------
# Medication & Virtual Pet Page
# ---------------------------
elif page == "Medication & Virtual Pet":
    st.title("GoldenAge Hub: Medication & Virtual Pet")

    # Open database connection
    conn = sqlite3.connect("goldenage.db")
    cursor = conn.cursor()

    # Ensure default user data exists
    cursor.execute("INSERT OR IGNORE INTO scores (user, score) VALUES ('default_user', 0)")
    cursor.execute("INSERT OR IGNORE INTO pet (user, food, mood) VALUES ('default_user', 0, 'happy')")
    conn.commit()

    # ---------------------------
    # Medication Reminder Section
    # ---------------------------
    st.subheader("Medication Reminder")
    med_name = st.text_input("Medication Name:")
    med_time = st.time_input("Time to Take Medicine:")

    if st.button("Add Medicine"):
        if med_name:
            cursor.execute(
                "INSERT INTO medication (medicine, time) VALUES (?, ?)",
                (med_name, med_time.strftime("%H:%M"))
            )
            conn.commit()
            st.success("Medication added successfully!")
            st.rerun()
        else:
            st.error("Please enter the name of the medicine")

    st.subheader("Today's Medication")
    cursor.execute("SELECT id, medicine, time, taken FROM medication")
    meds = cursor.fetchall()

    current_time = datetime.now().strftime("%H:%M")
    upcoming_meds = []

    # List all medication tasks and provide a "Mark as Taken" button
    for med in meds:
        col1, col2, col3 = st.columns(3)
        col1.write(f"{med[1]} at {med[2]}")
        med_time_obj = datetime.strptime(med[2], "%H:%M")
        reminder_time = (med_time_obj - timedelta(minutes=5)).strftime("%H:%M")

        if med[3] == 0:
            if col2.button("Mark as Taken", key=med[0]):
                cursor.execute("UPDATE medication SET taken = 1 WHERE id = ?", (med[0],))
                cursor.execute("UPDATE scores SET score = score + 10 WHERE user = 'default_user'")
                cursor.execute("UPDATE pet SET food = food + 1, mood = 'excited' WHERE user = 'default_user'")
                conn.commit()
                st.rerun()
            if current_time == reminder_time:
                upcoming_meds.append(med[1])
        else:
            col3.write("✅ Taken")

    if upcoming_meds:
        st.warning(f"Reminder: Time to take {', '.join(upcoming_meds)} in 5 minutes!")

    # ---------------------------
    # Virtual Pet Section
    # ---------------------------
    st.subheader("Your Virtual Pet")
    cursor.execute("SELECT food, mood FROM pet WHERE user = 'default_user'")
    result = cursor.fetchone()
    food_count, mood = result if result else (0, 'happy')

    pet_images = {
        "happy": "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif",
        "excited": "https://media.giphy.com/media/3oriO0OEd9QIDdllqo/giphy.gif",
        "hungry": "https://media.giphy.com/media/TgmiJ4AZ3HSiIqpOj6/giphy.gif"
    }
    st.image(pet_images.get(mood, pet_images["happy"]), width=200)
    st.write(f"Your pet is feeling {mood}!")
    st.write(f"You have {food_count} food for your pet!")

    if food_count > 0:
        if st.button("Feed your pet!"):
            cursor.execute("UPDATE pet SET food = food - 1, mood = 'happy' WHERE user = 'default_user'")
            conn.commit()
            st.success("You fed your pet!")
            st.rerun()
    else:
        cursor.execute("UPDATE pet SET mood = 'hungry' WHERE user = 'default_user'")
        conn.commit()
        st.warning("Your pet is hungry! Take your medication on time to earn more food!")

    conn.close()

# ---------------------------
# Arithmetic Game Page
# ---------------------------
elif page == "Arithmetic Game":
    st.title("Arithmetic Game")
    st.write("Answer the arithmetic question to earn food for your virtual pet!")

    # Initialize arithmetic question (store in session_state)
    if "operand1" not in st.session_state or "operand2" not in st.session_state:
        st.session_state.operand1 = random.randint(1, 20)
        st.session_state.operand2 = random.randint(1, 20)
        st.session_state.answer = st.session_state.operand1 + st.session_state.operand2

    st.write(f"Calculate: {st.session_state.operand1} + {st.session_state.operand2} = ?")
    user_answer = st.text_input("Your answer:")

    if st.button("Submit Answer"):
        try:
            if int(user_answer) == st.session_state.answer:
                st.success("Correct! You've earned 1 food reward!")
                # Update the pet table: add 1 food and update mood to excited
                conn = sqlite3.connect("goldenage.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE pet SET food = food + 1, mood = 'excited' WHERE user = 'default_user'")
                conn.commit()
                conn.close()
                # Reset arithmetic question
                st.session_state.operand1 = random.randint(1, 20)
                st.session_state.operand2 = random.randint(1, 20)
                st.session_state.answer = st.session_state.operand1 + st.session_state.operand2
            else:
                st.error("Incorrect answer, please try again!")
        except ValueError:
            st.error("Please enter a numerical answer.")
