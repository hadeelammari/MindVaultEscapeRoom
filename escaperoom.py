import openai
from openai import OpenAI
import streamlit as st
import os
import time
import datetime
import requests
import base64

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
    story_sections = {"Main_Story": ""}
    current_section = "Main_Story"
    
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
        
        # Parse riddle, answer, and hint
        riddle_parts = {}
        current_part = None
        
        for line in result.split('\n'):
            if line.startswith('Riddle:'):
                current_part = 'riddle'
                riddle_parts[current_part] = line.replace('Riddle:', '').strip()
            elif line.startswith('Answer:'):
                current_part = 'answer'
                riddle_parts[current_part] = line.replace('Answer:', '').strip().lower()
            elif line.startswith('Hint:'):
                current_part = 'hint'
                riddle_parts[current_part] = line.replace('Hint:', '').strip()
            elif current_part:
                riddle_parts[current_part] += ' ' + line.strip()
        
        riddles.append({
            "location": location,
            "riddle": riddle_parts.get('riddle', "A challenging riddle awaits..."),
            "answer": riddle_parts.get('answer', "unknown"),
            "hint": riddle_parts.get('hint', "Look carefully at the wording of the riddle.")
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
        st.error(f"Error calling ElevenLabs API: {e}")
        return None

# Function to create an audio player with the audio data
def get_audio_player(audio_data):
    if audio_data:
        b64 = base64.b64encode(audio_data).decode()
        return f'<audio autoplay controls><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    return ""

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
        .audio-player {{
            margin: 15px 0;
        }}
        .audio-controls {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 8px;
            margin-top: 10px;
        }}
        .audio-options {{
            display: flex;
            gap: 10px;
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
    for key in list(st.session_state.keys()):
        if key != 'audio_enabled':  # Preserve audio preference
            del st.session_state[key]
    
    # Reinitialize essential session state variables
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
if "audio_enabled" not in st.session_state:
    st.session_state.audio_enabled = True
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None
if "audio_cache" not in st.session_state:
    st.session_state.audio_cache = {}

# Set styles and the background if we have an image
if st.session_state.current_image:
    set_styles(st.session_state.current_image)
else:
    set_styles("")  # Default empty background

# Create main game container
main_container = st.container()

with main_container:
    # Custom title
    st.markdown("<h1 class='game-title'>The Mind Vault</h1><div class='game-sub-title'>A place of mystery and riddles</div><br/>", unsafe_allow_html=True)

    # Add an empty placeholder to hold the reset button
    reset_placeholder = st.empty()

    # Reset button (positioned outside main flow)
    with reset_placeholder.container():
        st.markdown("<div class='reset-button-container'>", unsafe_allow_html=True)
        if st.button("Reset Game"):
            reset_session()
        st.markdown("</div>", unsafe_allow_html=True)

    # Toggle for audio narration
    col1, col2 = st.columns([3, 1])
    with col2:
        st.session_state.audio_enabled = st.toggle("Enable Audio Narration", value=st.session_state.audio_enabled)

    # GAME COMPLETED SCREEN
    if st.session_state.game_completed:
        st.balloons()
        st.success("Congratulations! You've completed all the riddles!")
        
        # Calculate time taken
        if st.session_state.start_time:
            time_taken = time.time() - st.session_state.start_time
            st.markdown(f"<div class='timer-box'><h3>Time taken: {format_time(int(time_taken))}</h3></div>", unsafe_allow_html=True)
        
        # Generate victory audio
        if st.session_state.audio_enabled and "victory_audio" not in st.session_state.audio_cache:
            victory_text = "Congratulations! You've successfully completed all the riddles and escaped the mind vault. Your quick thinking and problem-solving skills have led you to victory!"
            with st.spinner("Generating audio..."):
                victory_audio = text_to_speech(victory_text)
                if victory_audio:
                    st.session_state.audio_cache["victory_audio"] = victory_audio
                    st.session_state.current_audio = victory_audio
        
        # Play victory audio if available
        if st.session_state.audio_enabled and "victory_audio" in st.session_state.audio_cache:
            st.markdown(
                f"<div class='audio-player'>{get_audio_player(st.session_state.audio_cache['victory_audio'])}</div>",
                unsafe_allow_html=True
            )
        
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
            st.session_state.audio_cache = {}  # Clear audio cache when theme changes

            # Generate storyline and riddles
            with st.spinner("Creating your adventure..."):
                try:
                    main_story, riddles = generate_escape_room_adventure(theme_choice)
                    st.session_state.main_story = main_story
                    st.session_state.riddles = riddles
                except Exception as e:
                    st.error(f"Error generating adventure: {str(e)}")
                    st.session_state.main_story = "An error occurred while creating your adventure."
                    st.session_state.riddles = []

            # Generate image
            with st.spinner("Creating themed background..."):
                try:
                    image_url = generate_image(theme_choice)
                    st.session_state.current_image = image_url
                    # Set styles again with the new image
                    set_styles(image_url)
                except Exception as e:
                    st.error(f"Error generating image: {str(e)}")
                    st.session_state.current_image = None

            # Generate intro audio if enabled
            if st.session_state.audio_enabled and st.session_state.main_story:
                with st.spinner("Generating narration..."):
                    intro_audio = text_to_speech(st.session_state.main_story)
                    if intro_audio:
                        st.session_state.audio_cache["intro"] = intro_audio
                        st.session_state.current_audio = intro_audio

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
                
                # Generate time's up audio
                if st.session_state.audio_enabled and "times_up" not in st.session_state.audio_cache:
                    times_up_text = "Time's up! You couldn't solve all the riddles in time. Don't worry, you can try again and see if you can beat the clock."
                    times_up_audio = text_to_speech(times_up_text)
                    if times_up_audio:
                        st.session_state.audio_cache["times_up"] = times_up_audio
                        st.session_state.current_audio = times_up_audio
                
                # Play time's up audio
                if st.session_state.audio_enabled and "times_up" in st.session_state.audio_cache:
                    st.markdown(
                        f"<div class='audio-player'>{get_audio_player(st.session_state.audio_cache['times_up'])}</div>",
                        unsafe_allow_html=True
                    )
                
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
                
                # Display audio player for main story
                if st.session_state.audio_enabled and "intro" in st.session_state.audio_cache:
                    st.markdown(
                        f"<div class='audio-player'>{get_audio_player(st.session_state.audio_cache['intro'])}</div>",
                        unsafe_allow_html=True
                    )
                
            # Display the current riddle if riddles exist and time remains
            if st.session_state.riddles and st.session_state.current_riddle_index < len(st.session_state.riddles):
                current_riddle = st.session_state.riddles[st.session_state.current_riddle_index]
                
                # Generate audio for current riddle if not already in cache
                riddle_audio_key = f"riddle_{st.session_state.current_riddle_index}"
                if st.session_state.audio_enabled and riddle_audio_key not in st.session_state.audio_cache:
                    riddle_text = f"Location: {current_riddle['location']}. Riddle: {current_riddle['riddle']}"
                    with st.spinner("Generating riddle narration..."):
                        riddle_audio = text_to_speech(riddle_text)
                        if riddle_audio:
                            st.session_state.audio_cache[riddle_audio_key] = riddle_audio
                            st.session_state.current_audio = riddle_audio
                
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
                
                # Play riddle audio
                if st.session_state.audio_enabled and riddle_audio_key in st.session_state.audio_cache:
                    st.markdown(
                        f"<div class='audio-player'>{get_audio_player(st.session_state.audio_cache[riddle_audio_key])}</div>",
                        unsafe_allow_html=True
                    )
                
                # Create error message container
                error_placeholder = st.empty()

                # Display hint if 3 or more wrong attempts
                if st.session_state.wrong_attempts >= 3:
                    st.markdown(f"<div class='hint-box'><h3>Hint:</h3>{current_riddle['hint']}</div>", unsafe_allow_html=True)
                    
                    # Generate hint audio if not already cached
                    hint_audio_key = f"hint_{st.session_state.current_riddle_index}"
                    if st.session_state.audio_enabled and hint_audio_key not in st.session_state.audio_cache:
                        hint_text = f"Here's a hint: {current_riddle['hint']}"
                        with st.spinner("Generating hint narration..."):
                            hint_audio = text_to_speech(hint_text)
                            if hint_audio:
                                st.session_state.audio_cache[hint_audio_key] = hint_audio
                                st.session_state.current_audio = hint_audio
                    
                    # Play hint audio
                    if st.session_state.audio_enabled and hint_audio_key in st.session_state.audio_cache:
                        st.markdown(
                            f"<div class='audio-player'>{get_audio_player(st.session_state.audio_cache[hint_audio_key])}</div>",
                            unsafe_allow_html=True
                        )
                
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
                    
                    # Check if answer is correct (case insensitive and multiple potential answers)
                    user_answer_lower = user_answer.strip().lower()
                    correct_answers = [ans.strip().lower() for ans in current_riddle['answer'].split(',')]
                    
                    if any(user_answer_lower == ans or user_answer_lower in ans for ans in correct_answers):
                        # Generate correct answer audio
                        if st.session_state.audio_enabled and "correct_answer" not in st.session_state.audio_cache:
                            correct_text = "Correct! Moving to the next challenge."
                            with st.spinner("Generating audio..."):
                                correct_audio = text_to_speech(correct_text)
                                if correct_audio:
                                    st.session_state.audio_cache["correct_answer"] = correct_audio
                                    st.session_state.current_audio = correct_audio
                        
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
                        
                        # Generate wrong answer audio if not already cached
                        wrong_audio_key = f"wrong_{min(st.session_state.wrong_attempts, 3)}"
                        if st.session_state.audio_enabled and wrong_audio_key not in st.session_state.audio_cache:
                            wrong_messages = [
                                "That's not correct. Try again!",
                                "Not quite right. Give it another try.",
                                "Still not correct. Think carefully about the riddle. A hint will appear soon."
                            ]
                            wrong_text = wrong_messages[min(st.session_state.wrong_attempts, 3) - 1]
                            with st.spinner("Generating audio..."):
                                wrong_audio = text_to_speech(wrong_text)
                                if wrong_audio:
                                    st.session_state.audio_cache[wrong_audio_key] = wrong_audio
                                    st.session_state.current_audio = wrong_audio
                        
                        # Set error message
                        if st.session_state.wrong_attempts >= 3:
                            st.session_state.error_message = "That's not correct. A hint has been provided above."
                            st.session_state.show_hint = True
                        else:
                            st.session_state.error_message = f"That's not correct. Try again! ({st.session_state.wrong_attempts}/3 attempts)"
                        
                        # Play wrong answer audio
                        if st.session_state.audio_enabled and wrong_audio_key in st.session_state.audio_cache:
                            st.markdown(
                                f"<div class='audio-player'>{get_audio_player(st.session_state.audio_cache[wrong_audio_key])}</div>",
                                unsafe_allow_html=True
                            )
                        
                        # Force a rerun to show the updated error message
                        st.rerun()
        elif not theme_choice:
            # No theme selected yet
            st.markdown(
                """
                <div class="game-container">
                    <h2>Welcome to The Mind Vault</h2>
                    <p>Select a theme above to begin your escape room adventure!</p>
                    <ul>
                        <li><strong>Mystery Mansion</strong>: Solve riddles in a haunted Victorian mansion</li>
                        <li><strong>Ancient Ruins</strong>: Uncover secrets in forgotten temple ruins</li>
                        <li><strong>Space Odyssey</strong>: Navigate puzzles on an abandoned space station</li>
                        <li><strong>Enchanted Forest</strong>: Decode magical riddles in a mystical woodland</li>
                    </ul>
                    <p>You'll have 5 minutes to solve all four riddles and escape!</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Store theme index for future use
            if theme_choice:
                themes = ["Mystery Mansion", "Ancient Ruins", "Space Odyssey", "Enchanted Forest"]
                if theme_choice in themes:
                    st.session_state.theme_index = themes.index(theme_choice) + 1  # +1 because index 0 is empty
            
            # Reset timer and progress when no theme is selected
            st.session_state.start_time = None
            st.session_state.current_riddle_index = 0