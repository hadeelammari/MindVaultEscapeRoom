import openai
from openai import OpenAI
import streamlit as st
import os
import time
import datetime
import requests


# Initialize OpenAI API client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "N2lVS1w4EtoT3dr4eOWO"

# Function to generate storyline and connected riddles
def generate_escape_room_adventure(theme, num_riddles=4):
    # Create a storyline that connects all riddles
    storyline_prompt = f"""Create a short, engaging escape room storyline related to the theme: {theme}.
    The story should connect {num_riddles} different locations or challenges, each with its own riddle.
    Make the storyline cohesive but each location/challenge distinct.
    Format your response as:
    Main_Story: [brief overall story]
    Location_1: [first location name: challenge description]
    Location_2: [second location name: challenge description]
    Location_3: [third location name: challenge description]
    Location_4: [fourth location name: challenge description]"""
    
    story_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are creating an immersive escape room adventure."},
                  {"role": "user", "content": storyline_prompt}],
        temperature=0.7,
        max_tokens=500
    )
    
    storyline_result = story_response.choices[0].message.content.strip()
    
    # Parse storyline sections
    story_sections = {}
    current_section = "Main_Story"
    story_sections[current_section] = ""
    
    for line in storyline_result.split('\n'):
        if any(f"Location_{i}:" in line for i in range(1, num_riddles+1)):
            current_section = line.split(':')[0].strip()
            story_sections[current_section] = line.split(':', 1)[1].strip() if ':' in line else ""
        elif "Main_Story:" in line:
            current_section = "Main_Story"
            story_sections[current_section] = line.split(':', 1)[1].strip() if ':' in line else ""
        else:
            story_sections[current_section] += " " + line.strip()
    
    # Generate distinct riddles for each location
    riddles = []
    for i in range(1, num_riddles+1):
        location_key = f"Location_{i}"
        location = story_sections.get(location_key, f"Challenge {i}")
        
        # Create a prompt that ensures the riddles are different
        previous_riddles = ""
        if riddles:
            previous_riddles = "Previous riddles generated (make this one different):\n"
            for j, prev_riddle in enumerate(riddles):
                previous_riddles += f"Riddle {j+1}: {prev_riddle['riddle']}\n"
        
        riddle_prompt = f"""Create a fun and engaging riddle for this escape room location: {location}
        The theme is: {theme}
        The riddle should be tricky but solvable and MUST BE DIFFERENT from any previous riddles.
        {previous_riddles}
        Format your response as:
        Riddle: [your riddle here]
        Answer: [clear answer]
        Hint: [specific, helpful hint]"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are creating unique, challenging riddles for each part of an escape room."},
                      {"role": "user", "content": riddle_prompt}],
            temperature=0.8,
            max_tokens=250
        )
        
        result = response.choices[0].message.content.strip()
        
        # Extract riddle, answer, and hint
        riddle = "A challenging riddle awaits..."
        answer = "unknown"
        hint = "Look carefully at the wording of the riddle."
        
        if "Riddle:" in result and "Answer:" in result:
            riddle_parts = result.split("Riddle:")
            riddle_with_answer = riddle_parts[1].strip()
            
            if "Answer:" in riddle_with_answer:
                riddle_answer_parts = riddle_with_answer.split("Answer:")
                riddle = riddle_answer_parts[0].strip()
                answer_with_hint = riddle_answer_parts[1].strip()
                
                if "Hint:" in answer_with_hint:
                    answer_hint_parts = answer_with_hint.split("Hint:")
                    answer = answer_hint_parts[0].strip().lower()
                    hint = answer_hint_parts[1].strip()
                else:
                    answer = answer_with_hint.strip().lower()
        
        riddles.append({
            "location": location,
            "riddle": riddle,
            "answer": answer,
            "hint": hint
        })
    
    return story_sections["Main_Story"], riddles

# Function to generate images using DALL·E
def generate_image(theme):
    response = client.images.generate(
        prompt=f"Create an immersive {theme} setting, with rich details and light colors suitable for a background for an escape room.",
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    return image_url

# ElevenLabs TTS Function
def text_to_speech(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise exception for non-200 status codes
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error calling ElevenLabs API: {e}")
        if response.content:
            print(f"Response details: {response.content}")
        return None

# Function to set CSS styles including the background image
def set_styles(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
        background-image: url("{image_url}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        }}

        .game-container {{
            background-color: rgba(255, 255, 255, 0.92);
            padding: 25px;
            border-radius: 12px;
            margin: 20px 0;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            display:none;

        }}
        .story-box {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #ff444c;
            margin: 15px 0;
            box-shadow: 0 3px 7px rgba(0, 0, 0, 0.1);
        }}
        .riddle-box {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #ff4b4b;
            margin: 15px 0;
            box-shadow: 0 3px 7px rgba(0, 0, 0, 0.1);
        }}
        .hint-box {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #ffcc00;
            margin: 15px 0;
            box-shadow: 0 3px 7px rgba(0, 0, 0, 0.1);
        }}
        .timer-box {{
            font-size: 24px;
            font-weight: bold;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            margin: 15px 0;
            box-shadow: 0 3px 7px rgba(0, 0, 0, 0.2);
        }}
        .timer-mystery {{
            background-color: #3a163d;
            color: #f2ce1b;
            border: 2px solid #6b2e70;
        }}
        .timer-ruins {{
            background-color: #7e6339;
            color: #e3dac9;
            border: 2px solid #594729;
        }}
        .timer-space {{
            background-color: #0c164f;
            color: #00ffff;
            border: 2px solid #273c75;
        }}
        .timer-forest {{
            background-color: #1e4d2b;
            color: #b6ff9c;
            border: 2px solid #3e7e46;
        }}
        .progress-bar {{
            background-color: #f0f0f0;
            border-radius: 8px;
            padding: 3px;
            margin: 15px 0;
            box-shadow: 0 3px 7px rgba(0, 0, 0, 0.1);
        }}
        .progress-fill {{
            background-color: #4CAF50;
            height: 24px;
            border-radius: 5px;
            text-align: center;
            line-height: 24px;
            color: white;
            font-weight: bold;
            transition: width 0.3s;
        }}
        .game-title {{
            font-family: 'Trebuchet MS', sans-serif;
            text-align: center;
            font-size: 52px;
            font-weight: bold;
            color: #1a1a1a;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4), 0 0 10px rgba(255, 255, 255, 0.5);
            letter-spacing: 2px;
        }}
        .game-sub-title {{
            font-family: 'Trebuchet MS', sans-serif;
            text-align: center;
            font-size: 20px;
            color: #1a1a1a;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4), 0 0 10px rgba(255, 255, 255, 0.5);
        }}
        .high-contrast-text {{
            color: black;
            text-shadow: 
                0px 0px 3px white,
                0px 0px 6px white,
                0px 0px 9px white;
            font-weight: bold;
        }}
        .centered-button {{
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }}
        .stButton > button {{
            font-weight: bold;
            padding: 10px 25px;
            border-radius: 6px;
        }}
        /* Improve reset button position */
        .reset-button-container {{
            position: absolute;
            top: 20px;
            right: 30px;
        }}
        /* Hide empty text area */
        .stTextArea, .stText {{
            display: none;
        }}
        /* Theme selector styling */
        .stSelectbox [data-baseweb=select] {{
            background-color: white;
        }}
        /* User input styling */
        .stTextInput > div > div > input {{
            border: 2px solid #4a4a4a;
            font-size: 18px;
            padding: 8px 12px;
        }}
        .error-message{{
            padding: 10px;
            border-radius: 5px;
            background-color: #FF7F7F;
            color: #800000; 
            font-weight: bold;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Format time remaining
def format_time(seconds):
    return f"{seconds // 60:02d}:{seconds % 60:02d}"

# Get timer style based on theme
def get_timer_class(theme):
    theme_lower = theme.lower()
    if "mystery" in theme_lower:
        return "timer-mystery"
    elif "ruins" in theme_lower:
        return "timer-ruins"
    elif "space" in theme_lower:
        return "timer-space"
    elif "forest" in theme_lower:
        return "timer-forest"
    else:
        return "timer-mystery"  # default

def reset_session():
    st.session_state.game_completed = False
    st.session_state.current_theme = None
    st.session_state.theme_index = 0 
    st.session_state.riddles = []
    st.session_state.main_story = None
    st.session_state.current_riddle_index = 0
    st.session_state.current_image = None
    st.session_state.start_time = None
    st.session_state.wrong_attempts = 0
    st.session_state.previous_answer = ""
    st.session_state.error_message = ""
    st.session_state.show_hint = False
    st.rerun()
    
# Initialize session state
if "current_theme" not in st.session_state:
    st.session_state.current_theme = None
if 'theme_index' not in st.session_state:
    st.session_state.theme_index = 0
if "game_completed" not in st.session_state:
    st.session_state.game_completed = False
if "riddles" not in st.session_state:
    st.session_state.riddles = []
if "main_story" not in st.session_state:
    st.session_state.main_story = None
if "current_riddle_index" not in st.session_state:
    st.session_state.current_riddle_index = 0
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "time_limit" not in st.session_state:
    st.session_state.time_limit = 300  # 5 minutes in seconds
if "wrong_attempts" not in st.session_state:
    st.session_state.wrong_attempts = 0
if "previous_answer" not in st.session_state:
    st.session_state.previous_answer = ""
if "show_hint" not in st.session_state:
    st.session_state.show_hint = False
if "error_message" not in st.session_state:
    st.session_state.error_message = ""

# Set styles and the background if we have an image
set_styles(st.session_state.current_image)

# Add an empty placeholder to hold the reset button
reset_placeholder = st.empty()

# Create main game container
st.markdown("<div class='game-container'>", unsafe_allow_html=True)

# Custom title
st.markdown("<h1 class='game-title'>The Mind Vault</h1><div class='game-sub-title'>A place of mystery and riddles</div><br/>", unsafe_allow_html=True)

# Reset button (positioned outside main flow)
with reset_placeholder.container():
    st.markdown("<div class='reset-button-container'>", unsafe_allow_html=True)
    if st.button("Reset Game"):
        reset_session()
    st.markdown("</div>", unsafe_allow_html=True)

# GAME COMPLETED SCREEN
if st.session_state.game_completed:
    st.balloons()
    st.success("Congratulations! You've completed all the riddles!")
    
    # Calculate time taken
    if st.session_state.start_time:
        time_taken = time.time() - st.session_state.start_time
        st.markdown(f"<div class='timer-box'><h3>Time taken: {format_time(int(time_taken))}</h3></div>", unsafe_allow_html=True)
    
    # Center the start new game button
    st.markdown("<div class='centered-button'>", unsafe_allow_html=True)
    if st.button("Start New Game"):    
        reset_session()
    st.markdown("</div>", unsafe_allow_html=True)

# ACTIVE GAME SCREEN
else:
    # Choose a theme with an empty initial selection
    theme_choice = st.selectbox("Select a theme", [""] + ["Mystery Mansion", "Ancient Ruins", "Space Odyssey", "Enchanted Forest"], index=st.session_state.theme_index)
   
    if theme_choice and (theme_choice != st.session_state.current_theme or not st.session_state.riddles):
        st.session_state.current_theme = theme_choice
        st.session_state.start_time = time.time()  # Reset timer when theme changes
        st.session_state.wrong_attempts = 0  # Reset wrong attempts
        st.session_state.current_riddle_index = 0  # Reset to first riddle
        st.session_state.error_message = ""
        st.session_state.show_hint = False

        # Generate storyline and riddles
        with st.spinner("Creating your adventure..."):
            main_story, riddles = generate_escape_room_adventure(theme_choice)
            st.session_state.main_story = main_story
            st.session_state.riddles = riddles

        # Generate image
        with st.spinner("Creating themed background..."):
            try:
                image_url = generate_image(theme_choice)
                st.session_state.current_image = image_url
                # Refresh the page to apply the background
                st.rerun()
            except Exception as e:
                st.error(f"Error generating image: {str(e)}")
                st.session_state.current_image = None

    # Display timer if we have a theme
    if st.session_state.current_theme and st.session_state.start_time:
        # Calculate time remaining
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, st.session_state.time_limit - int(elapsed))
        
        # Display themed timer
        timer_class = get_timer_class(st.session_state.current_theme)
        st.markdown(f"<div class='timer-box {timer_class}'>Time Remaining: {format_time(remaining)}</div>", unsafe_allow_html=True)
        
        # Display progress bar
        progress_percentage = (st.session_state.current_riddle_index / 4) * 100
        st.markdown(
            f"""
            <div class='progress-bar'>
                <div class='progress-fill' style='width: {progress_percentage}%;'>
                    {st.session_state.current_riddle_index}/4 Riddles
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # Check if time's up
        if remaining <= 0:
            st.error("Time's up! You couldn't solve the riddles in time.")
            st.markdown("<div class='centered-button'>", unsafe_allow_html=True)
            if st.button("Try Again"):
                st.session_state.start_time = time.time()  # Reset timer
                st.session_state.wrong_attempts = 0  # Reset wrong attempts
                st.session_state.error_message = ""
                st.session_state.show_hint = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    
        # Display main story only on the first riddle
        elif st.session_state.current_riddle_index == 0 and st.session_state.main_story:
            st.markdown(f"<div class='story-box'><h3>Your Adventure Begins:</h3>{st.session_state.main_story}</div>", unsafe_allow_html=True)
            
        # Display the current riddle if riddles exist and time remains
        if st.session_state.riddles and st.session_state.current_riddle_index < len(st.session_state.riddles):
            current_riddle = st.session_state.riddles[st.session_state.current_riddle_index]
            
            # Display location story and riddle together
            st.markdown(
                f"""
                <div class='riddle-box'>
                    <p class='location-story'>{current_riddle['location']}</p>
                    <h4>Riddle {st.session_state.current_riddle_index + 1} of 4:</h4>
                    <p class='riddle-text'>{current_riddle['riddle']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Create error message container
            error_placeholder = st.empty()

            # Display hint if 3 or more wrong attempts
            if st.session_state.wrong_attempts >= 3:
                st.markdown(f"<div class='hint-box'><h3>Hint:</h3>{current_riddle['hint']}</div>", unsafe_allow_html=True)
            
            # Use placeholder text in input box instead of label
            user_answer = st.text_input("User Answer", placeholder="Enter your answer here and press Enter...", key=f"answer_input_{st.session_state.current_riddle_index}", label_visibility="collapsed")

            # Display any existing error message
            if st.session_state.error_message:
                error_placeholder.markdown(f"""
                <div class="error-message">
                {st.session_state.error_message}
                </div>
                """, unsafe_allow_html=True)
               
            # Check if Enter was pressed (when the input value changes)
            if user_answer and user_answer != st.session_state.previous_answer:
                # Store current answer to detect changes
                st.session_state.previous_answer = user_answer
                
                # Check if answer is correct
                if user_answer.strip().lower() in current_riddle['answer']:
                    # Show success message
                    # st.success("Correct! Moving to the next riddle...")
                    
                    # Move to the next riddle
                    st.session_state.current_riddle_index += 1
                    st.session_state.wrong_attempts = 0  # Reset wrong attempts for next riddle
                    st.session_state.previous_answer = ""  # Reset previous answer
                    st.session_state.error_message = ""   # Clear error message
                    st.session_state.show_hint = False    # Hide hint for next riddle
                        
                    # Check if all riddles are completed
                    if st.session_state.current_riddle_index >= len(st.session_state.riddles):
                        st.session_state.game_completed = True
                    
                    # Rerun to update the page with new riddle or completion screen
                    st.rerun()
                else:
                    # Wrong answer
                    st.session_state.wrong_attempts += 1
                    # Update error message based on wrong attempts
                    if st.session_state.wrong_attempts == 1:
                        error_message = f"Incorrect! Try again. (Attempt {st.session_state.wrong_attempts})"
                    elif st.session_state.wrong_attempts == 2:
                        error_message = f"Incorrect! Try again. (Attempt {st.session_state.wrong_attempts}). One more wrong answer and you'll get a hint!"
                    elif st.session_state.wrong_attempts >= 3:
                        error_message = f"Incorrect! Try again. (Attempt {st.session_state.wrong_attempts})"
                        st.session_state.show_hint = True  # Show hint after 3 wrong attempts
                    
                    error_placeholder.markdown(f"""
                    <div class="error-message">
                    {error_message}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display error immediately and also save to session state
                    st.session_state.error_message = error_message
                    
                    # Show hint after 3 wrong attempts
                    if st.session_state.wrong_attempts >= 3:
                        st.session_state.show_hint = True
                        st.rerun()  # Only rerun if we need to show a hint

    # Add auto-refresh mechanism for timer updates using Streamlit's native approach
    if st.session_state.current_theme and st.session_state.start_time and not st.session_state.game_completed:
        # Create an empty element that will trigger a rerun
        placeholder = st.empty()
        
        # Only rerun if there's time left
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, st.session_state.time_limit - int(elapsed))
        
        if remaining > 0:
            # Wait for a short time, then rerun
            time.sleep(1)
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Add a high-contrast attribution/footer
st.markdown("<p class='high-contrast-text' style='text-align: center; margin-top: 20px;'>The Mind Vault - Escape Room &copy; 2025</p>", unsafe_allow_html=True)