import speech_recognition as sr
import pyttsx3
import webbrowser
import urllib.parse
import subprocess
import random
import json
import os
from plyer import notification
import threading
import time
import requests
import shutil
import glob

MEMORY_FILE = 'nova_memory.json'

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

#The first time setup function
def first_time_setup():
    speak("Hello! I am Nova, your personal voice assistant.")
    speak("It seems like this is our first time meeting. I would love to get to know you.")

    # Ask for first name
    speak("What is your first name?")
    first_name = listen()
    while first_name is None:
        speak("Sorry, I did not catch that. What is your first name?")
        first_name = listen()

    # Ask for surname
    speak(f"Nice to meet you {first_name}! What is your surname?")
    surname = listen()
    while surname is None:
        speak("Sorry, could you repeat your surname?")
        surname = listen()

    # Ask for gender
    speak("Are you male or female?")
    gender = listen()
    while gender is None or ('male' not in gender and 'female' not in gender):
        speak("Please say male or female.")
        gender = listen()

    # Set title based on gender
    if 'female' in gender:
        title = "Ma'am"
    else:
        title = "Sir"

    # Ask for date of birth
    speak("What is your date of birth? Please say it like this — January 15 1990.")
    dob = listen()
    while dob is None:
        speak("Sorry, could you repeat your date of birth?")
        dob = listen()

    # Save everything to memory
    memory['first_name'] = first_name
    memory['surname']    = surname
    memory['gender']     = gender
    memory['title']      = title
    memory['dob']        = dob
    memory['setup_done'] = True
    save_memory(memory)

    speak(f"Thank you! It is wonderful to meet you {title} {first_name} {surname}. "
          f"I will remember everything you have told me.")

    # Ask how they are feeling right away
    speak(f"Before we get started {title} {first_name}, "
          f"how are you feeling today?")
    feeling = listen()
    if feeling:
        mood = detect_mood(feeling)
        if mood:
            respond_to_mood(mood)
        else:
            speak(f"That is good to know {title} {first_name}. "
                  f"I am here whenever you need me!")

#Birthday checker function
def check_birthday():
    if 'dob' not in memory:
        return
    
    import datetime
    today = datetime.datetime.now()
    dob = memory['dob'].lower()
    
    months = {
        'january': 1,  'february': 2,  'march': 3,  
        'april': 4,    'may': 5,       'june': 6,
        'july': 7,     'uagust': 8,    'september': 9,
        'october': 10, 'november': 11, 'december': 12
    }
    
    for month_name, month_num in months.items():
        if month_name in dob and today.month == month_num:
            if str(today.day) in dob:
                name       = memory.get('first_name', 'friend')
                title_word = memory.get('title', '')
                speak(f"Happy Birthday {title_word} {name}!"
                      f"I hope you have a wonderful day!")
                notification.notify(
                    title="Happy Birthday!",
                    message=f"Nova wishes you a very happy birthday "
                            f"{title_word} {name}!",
                    app_name="Nova Voice Assistant",
                    timeout=10
                )
             
def morning_briefing():
    import datetime
    name       = memory.get('first_name', 'friend')
    title_word = memory.get('title', '')
    now        = datetime.datetime.now()

    # Greeting based on time of day
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # Opening greeting
    speak(f"{greeting} {title_word} {name}! "
          f"Welcome to your daily briefing.")

    # Today's date
    today_str = now.strftime("%A, %B %d %Y")
    speak(f"Today is {today_str}.")

    # Check birthday
    if 'dob' in memory:
        dob = memory['dob'].lower()
        months = {
            'january': 1,  'february': 2,  'march': 3,
            'april': 4,    'may': 5,       'june': 6,
            'july': 7,     'august': 8,    'september': 9,
            'october': 10, 'november': 11, 'december': 12
        }
        for month_name, month_num in months.items():
            if month_name in dob and now.month == month_num:
                if str(now.day) in dob:
                    speak(f"And {title_word} {name} — "
                          f"today is your birthday! "
                          f"Happy birthday to you! "
                          f"I hope today is absolutely wonderful!")

    # Today's appointments
    if 'appointments' not in memory or not memory['appointments']:
        speak("You have no appointments scheduled for today. "
              "Enjoy your free day!")
    else:
        todays = []
        for appt in memory['appointments']:
            try:
                appt_date = datetime.datetime.strptime(
                    appt['date'], "%Y-%m-%d"
                )
                if (appt_date.day   == now.day and
                    appt_date.month == now.month and
                    appt_date.year  == now.year):
                    todays.append(appt)
            except ValueError:
                continue

        if not todays:
            speak("You have no appointments scheduled for today.")
        elif len(todays) == 1:
            speak(f"You have one appointment today — "
                  f"{todays[0]['title']} at {todays[0]['time']}.")
        else:
            speak(f"You have {len(todays)} appointments today.")
            for appt in todays:
                speak(f"{appt['title']} at {appt['time']}.")

    # Weather update
    speak("Now let me check the weather for you.")
    weather = get_weather()
    if weather:
        speak(f"Currently in {WEATHER_CITY} it is "
              f"{weather['temp']} degrees celsius "
              f"and {weather['description']}.")
        speak(f"It feels like {weather['feels_like']} degrees.")

        if weather['temp'] >= 30:
            speak("It is going to be a hot one today. "
                  "Stay hydrated!")
        elif weather['temp'] <= 10:
            speak("Bundle up today — it is quite cold outside!")
        elif 'rain' in weather['description']:
            speak("There is a chance of rain today. "
                  "Keep an umbrella handy!")
        else:
            speak("It looks like a lovely day ahead!")

    # Motivational quote
    quote = random.choice(QUOTES)
    speak(f"And here is something to keep in mind today — {quote}")

    # Closing
    speak(f"That is your briefing for today {title_word} {name}. "
          f"Have a wonderful and productive day. "
          f"I am here whenever you need me!")

def detect_mood(command):
    command_lower = command.lower()
    for mood, keywords in MOODS.items():
        for keyword in keywords:
            if keyword in command_lower:
                return mood
    return None


def respond_to_mood(mood):
    name       = memory.get('first_name', 'friend')
    title_word = memory.get('title', '')
    global voice_rate, voice_volume

    if mood == 'stressed':
        # Slow Nova down and make her calming
        voice_rate = 145
        speak(f"I can hear that you are feeling stressed "
              f"{title_word} {name}. "
              f"Take a slow deep breath with me. "
              f"Breathe in... and breathe out. "
              f"You are doing well and you will get through this. "
              f"Would you like to talk about what is on your mind?")

    elif mood == 'tired':
        voice_rate = 150
        speak(f"It sounds like you need some rest "
              f"{title_word} {name}. "
              f"Your body and mind work hard for you every day. "
              f"Make sure you take breaks and look after yourself. "
              f"Is there anything I can help you with right now?")

    elif mood == 'happy':
        voice_rate = 190
        speak(f"That is absolutely wonderful to hear "
              f"{title_word} {name}! "
              f"Your positive energy is contagious! "
              f"I love it when you are in a great mood. "
              f"Let us make the most of this amazing day together!")

    elif mood == 'sad':
        voice_rate = 145
        speak(f"I am sorry to hear you are feeling sad "
              f"{title_word} {name}. "
              f"It is completely okay to feel this way sometimes. "
              f"Just know that I am always here for you. "
              f"Things will get better. "
              f"Would you like me to play something to cheer you up?")

    elif mood == 'angry':
        voice_rate = 155
        speak(f"I understand {title_word} {name}. "
              f"It is okay to feel frustrated sometimes. "
              f"Take a moment to breathe. "
              f"Whatever happened, you are strong enough to handle it. "
              f"Would you like to talk about it?")

    elif mood == 'bored':
        voice_rate = 180
        speak(f"Feeling bored {title_word} {name}? "
              f"Let me fix that! "
              f"I could tell you a joke, "
              f"search for something interesting online, "
              f"or open an app for you. "
              f"What sounds good?")
    
    #Return VOice back to normal after response
    voice_rate = 175
    
def get_weather():
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={WEATHER_CITY}"
            f"&appid={WEATHER_API_KEY}"
            f"&units=metric"
        )
        response = requests.get(url, timeout=5)
        data     = response.json()

        if response.status_code != 200:
            speak("I could not fetch the weather right now.")
            return None

        temp        = round(data['main']['temp'])
        feels_like  = round(data['main']['feels_like'])
        humidity    = data['main']['humidity']
        description = data['weather'][0]['description']
        wind_speed  = round(data['wind']['speed'])

        return {
            'temp':        temp,
            'feels_like':  feels_like,
            'humidity':    humidity,
            'description': description,
            'wind_speed':  wind_speed
        }

    except requests.exceptions.ConnectionError:
        speak("I could not connect to the weather service. "
              "Please check your internet connection.")
        return None
    except Exception:
        speak("Something went wrong fetching the weather.")
        return None
       
def find_file(filename):
    speak(f"Searching for {filename} on your PC. "
          f"Please give me a moment.")
    
    # Search common locations first for speed
    search_locations = [
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Documents"),
        os.path.expanduser("~\\Downloads"),
        os.path.expanduser("~\\Pictures"),
        os.path.expanduser("~\\Music"),
        os.path.expanduser("~\\Videos"),
    ]
    
    found_files = []
    
    for location in search_locations:
        pattern = os.path.join(location, "**", f"*{filename}*")
        results = glob.glob(pattern, recursive=True)
        found_files.extend(results)
    
    if not found_files:
        speak(f"I could not find any file matching "
              f"{filename} in your common folders.")
        return None
    elif len(found_files) == 1:
        speak(f"I found it! The file is located at "
              f"{found_files[0]}")
        return found_files[0]
    else:
        speak(f"I found {len(found_files)} files matching "
              f"{filename}. Here are the first 3.")
        for f in found_files[:3]:
            speak(f)
        return found_files[0]


def create_folder(folder_name, location=None):
    if location is None:
        location = os.path.expanduser("~\\Documents")

    full_path = os.path.join(location, folder_name)

    if os.path.exists(full_path):
        speak(f"A folder called {folder_name} already exists there.")
        return

    os.makedirs(full_path)
    speak(f"Done! I have created a folder called "
          f"{folder_name} in your Documents.")


def list_files(folder_name):
    # Map spoken names to real folder paths
    folder_map = {
        'desktop':   os.path.expanduser("~\\Desktop"),
        'documents': os.path.expanduser("~\\Documents"),
        'downloads': os.path.expanduser("~\\Downloads"),
        'pictures':  os.path.expanduser("~\\Pictures"),
        'music':     os.path.expanduser("~\\Music"),
        'videos':    os.path.expanduser("~\\Videos"),
    }

    folder_path = None
    for key, path in folder_map.items():
        if key in folder_name.lower():
            folder_path = path
            break

    if folder_path is None:
        speak(f"I could not find a folder called {folder_name}. "
              f"Try saying desktop, documents or downloads.")
        return

    try:
        items = os.listdir(folder_path)
        if not items:
            speak(f"The {folder_name} folder is empty.")
            return

        files   = [i for i in items if os.path.isfile(
                   os.path.join(folder_path, i))]
        folders = [i for i in items if os.path.isdir(
                   os.path.join(folder_path, i))]

        speak(f"In your {folder_name} I found "
              f"{len(files)} files and {len(folders)} folders.")

        if files:
            speak("Here are the first 5 files.")
            for f in files[:5]:
                speak(f)
    except PermissionError:
        speak(f"I do not have permission to access that folder.")


def move_file(filename, destination_name):
    # Map spoken destination to real path
    dest_map = {
        'desktop':   os.path.expanduser("~\\Desktop"),
        'documents': os.path.expanduser("~\\Documents"),
        'downloads': os.path.expanduser("~\\Downloads"),
        'pictures':  os.path.expanduser("~\\Pictures"),
        'music':     os.path.expanduser("~\\Music"),
        'videos':    os.path.expanduser("~\\Videos"),
    }

    dest_path = None
    for key, path in dest_map.items():
        if key in destination_name.lower():
            dest_path = path
            break

    if dest_path is None:
        speak(f"I do not recognise {destination_name} as a destination. "
              f"Try saying desktop, documents or downloads.")
        return

    source = find_file(filename)
    if source is None:
        return

    try:
        dest_file = os.path.join(dest_path,
                                 os.path.basename(source))
        shutil.move(source, dest_file)
        speak(f"Done! I have moved {filename} to your "
              f"{destination_name}.")
    except Exception as e:
        speak(f"Sorry I could not move that file. "
              f"Please make sure it is not open.")


def delete_file(filename):
    source = find_file(filename)
    if source is None:
        return

    name       = memory.get('first_name', 'friend')
    title_word = memory.get('title', '')

    speak(f"I found {filename}. Are you sure you want to "
          f"delete it {title_word} {name}? "
          f"This cannot be undone. Say yes to confirm.")
    confirm = listen()

    if confirm and 'yes' in confirm:
        try:
            os.remove(source)
            speak(f"Done. {filename} has been permanently deleted.")
        except Exception:
            speak(f"Sorry I could not delete that file. "
                  f"Please make sure it is not open.")
    else:
        speak(f"No problem. I have left {filename} untouched.")


def rename_file(old_name, new_name):
    source = find_file(old_name)
    if source is None:
        return

    folder   = os.path.dirname(source)
    ext      = os.path.splitext(source)[1]
    new_path = os.path.join(folder, new_name + ext)

    try:
        os.rename(source, new_path)
        speak(f"Done! I have renamed {old_name} to {new_name}.")
    except Exception:
        speak(f"Sorry I could not rename that file. "
              f"Please make sure it is not open.")
       
#Appointment system function: saves user's appointments
def save_appointment(appt_title, date_str, time_str):
    if 'appointments' not in memory:
        memory['appointments'] = []
        
    memory['appointments'].append({
        'title': appt_title,
        'date': date_str,
        'time': time_str
    })
    save_memory(memory)
    
    
def check_appointments():
    while True:
        if 'appointments' not in memory:
            time.sleep(60)
            continue
        
        import datetime
        now        = datetime.datetime.now()
        name       = memory.get('first_name', 'friend')
        title_word = memory.get('title', '')
        
        for appointment in memory['appointments']:
            appt_str = appointment['date'] + ' ' + appointment['time']
            
            try:
                appt_time = datetime.datetime.strptime(
                    appt_str, "%Y-%m-%d %H:%M"
                )
            except ValueError:
                continue
            
            minutes_left = (appt_time - now). total_seconds() / 60
            
            #2 Hours before
            if 119 <= minutes_left <= 121:
                speak(f"Hey {title_word} {name}, just a heads up! "
                      f"You have {appointment['title']} in 2 hours. "
                      f"You might want to start getting ready!")
                notification.notify(
                    title="Upcoming appointment",
                    message=f"{appointment['title']} is in 2 hours!",
                    app_name="Nova Voice Assistant",
                    timeout=10
                )
        
             # 30 minutes before
            elif 29 <= minutes_left <= 31:
                speak(f"{title_word} {name}, your {appointment['title']} "
                      f"is in 30 minutes. Please do not forget!")
                notification.notify(
                    title="Appointment soon!",
                    message=f"{appointment['title']} starts in 30 minutes!",
                    app_name="Nova Voice Assistant",
                    timeout=10
                )

            # 5 minutes before
            elif 4 <= minutes_left <= 6:
                speak(f"Hey {title_word} {name}! "
                      f"Your {appointment['title']} is starting in just "
                      f"5 minutes. Time to go!")
                notification.notify(
                    title="Starting now!",
                    message=f"{appointment['title']} starts in 5 minutes!",
                    app_name="Nova Voice Assistant",
                    timeout=10
                )
                
            # On time for the appointment
            elif 0 <= minutes_left <= 1:
                speak(f"Hey {title_word} {name}! "
                      f"Your {appointment['title']} is starting now {title_word} {name} "
                      f"Wanted to check if you are already there. Goodluck and Enjoy {appointment['title']}!")
                notification.notify(
                    title="Starting now!",
                    message=f"{appointment['title']} starts NOW {title_word} {name}!",
                    app_name="Nova Voice Assistant",
                    timeout=10
                )
        time.sleep(60)
        
#Load Nova's memory when she starts up
memory = load_memory()

APPS = {
    "file explorer": "explorer.exe",
    "calculator":    "calc.exe",
    "vs code":       "C:\\Users\\Kieran Tyron\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
    "notepad":       "notepad.exe",
    "android studio":"C:\\Program Files\\Android\\Android Studio\\bin\\studio64.exe",
}

# Jokes stored as pairs — setup and punchline separately
JOKES = [
    ("Why do programmers prefer dark mode?", "Because light attracts bugs!"),
    ("Why did the computer go to the doctor?", "Because it had a virus!"),
    ("Why do Java developers wear glasses?", "Because they don't C sharp!"),
    ("Why was the math book sad?", "Because it had too many problems!"),
    ("What do you call a computer that sings?", "A Dell!"),
    ("Why did the developer go broke?", "Because he used up all his cache!"),
    ("What is a computer's favourite snack?", "Microchips!"),
    ("Why did the smartphone go to school?", "To improve its apps!"),
    ("Why do computers never get hungry?", "Because they already have plenty of bytes!"),
    ("Why did the programmer quit his job?", "Because he did not get arrays!"),
]

QUOTES = [
    "Today is a great day to do something amazing.",
    "Believe in yourself. You are capable of more than you know.",
    "Every day is a second chance. Make it count.",
    "Small steps every day lead to big results.",
    "You have got this. Now go out there and make it happen.",
    "Success is not given. It is earned one day at a time.",
    "The best time to start was yesterday. The second best time is right now.",
    "Your potential is limitless. Never stop growing.",
    "Great things never come from comfort zones.",
    "Today is your day. Own it completely.",
]

# Mood keyword detection
MOODS = {
    'stressed': [
        'stressed', 'stress', 'overwhelmed', 'pressure',
        'anxious', 'anxiety', 'worried', 'nervous', 'panic'
    ],
    'tired': [
        'tired', 'exhausted', 'sleepy', 'fatigue',
        'drained', 'worn out', 'no energy', 'sleepy'
    ],
    'happy': [
        'happy', 'excited', 'great', 'amazing', 'fantastic',
        'wonderful', 'excellent', 'brilliant', 'awesome', 'joyful'
    ],
    'sad': [
        'sad', 'unhappy', 'depressed', 'down', 'upset',
        'miserable', 'heartbroken', 'lonely', 'hurt', 'crying'
    ],
    'angry': [
        'angry', 'furious', 'annoyed', 'frustrated',
        'irritated', 'mad', 'rage', 'hate', 'livid'
    ],
    'bored': [
        'bored', 'boring', 'nothing to do', 'dull',
        'uninterested', 'fed up', 'restless'
    ],
}

#Weather settings
WEATHER_API_KEY = "a0a17ab37806474ca2a00bc4fd39be33"
WEATHER_CITY    = "Cape Town"

#Lock that prevents two parts of Nova speaking at the same time
speak_lock = threading.Lock()

#Function that makes Nova Speak
def speak(text):
    print(f"Nova: {text}")
    with speak_lock:
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 0.5)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    
#Test Nova's voice
#speak("Hello! I am Nova, your personal voice assistant.")

#Setup the microphone listener
recognizer = sr.Recognizer()
microphone = sr.Microphone()
recognizer.energy_threshold = 400
recognizer.dynamic_energy_threshold = False
recognizer.pause_threshold = 1.0
recognizer.non_speaking_duration = 0.5

# Run noise adjustment once at startup instead of every listen
def calibrate_microphone():
    print("Calibrating microphone, please wait...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    # Lock threshold between 350 and 600 — safe range for most rooms
    recognizer.energy_threshold = max(350, min(recognizer.energy_threshold, 600))
    print(f"Microphone ready! Sensitivity set to {int(recognizer.energy_threshold)}")

def listen():
    with microphone as source:
        print("Listening...")
        try:
            audio = recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=15
            )
        except sr.WaitTimeoutError:
            return None

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"You said: {text}")
        return text.lower()

    except sr.UnknownValueError:
        #speak("Sorry, I did not catch that. Please try again.")
        return None

    except sr.RequestError:
        speak("I am having trouble connecting. Check your internet.")
        return None
    
#Test Nova's ears
#speak("Say something and I will repeat it back.")
#result = listen()
#if result:
#    speak(f"You said: {result}")

def handle_command(command):
    global memory
    mood = detect_mood(command)
    if mood:
        respond_to_mood(mood)
        return
    
    #Tell the time
    if 'time' in command:
        import datetime
        time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {time}")
        
    #Tell the date 
    elif 'date' in command:
        import datetime
        date = datetime.datetime.now().strftime("%A, %B %d %Y")
        speak(f"Today is {date}")
        
    #Greet the user
    elif 'hello' in command or 'hi' in command:
        speak("Hello! How can I help you today?")
    
    #Morning briefing
    elif any(phrase in command for phrase in [
        'good morning', 'morning briefing',
        'daily briefing', 'good afternoon',
        'good evening', 'briefing'
    ]):
        morning_briefing()
    
    # Weather
    elif any(word in command for word in
             ['weather', 'temperature', 'how hot',
              'how cold', 'outside', 'raining']):
        name       = memory.get('first_name', 'friend')
        title_word = memory.get('title', '')
        weather    = get_weather()

        if weather:
            speak(f"Here is the current weather in "
                  f"{WEATHER_CITY} {title_word} {name}.")
            speak(f"It is {weather['temp']} degrees celsius "
                  f"and {weather['description']}.")
            speak(f"It feels like {weather['feels_like']} degrees "
                  f"with a humidity of {weather['humidity']} percent.")
            speak(f"Wind speed is {weather['wind_speed']} "
                  f"metres per second.")

            # Practical advice based on weather
            if weather['temp'] >= 30:
                speak("It is quite hot today. "
                      "Please stay hydrated and wear sunscreen!")
            elif weather['temp'] <= 10:
                speak("It is quite cold today. "
                      "Make sure you wear a warm jacket!")
            elif 'rain' in weather['description']:
                speak("It looks like rain today. "
                      "Do not forget your umbrella!")
            else:
                speak("Sounds like a lovely day to go outside!")
    
    #Remeber something
    elif 'remember' in command:
        speak("What would you like me to remember?")
        thing = listen()
        if thing:
            #Use the current time as a unique key
            import datetime
            key = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            memory[key] = thing
            save_memory(memory)
            speak(f"Got it! I will remember that {thing}")
            
    #Recall everything Nova remembers
    elif 'what do you remember' in command or 'what did we last speak about' in command or 'how is my schedule looking like tomorrow' in command:
        if memory:
            speak(f"I currently remember {len(memory)} things. Here they are.")
            for item in memory.values():
                speak(item)
        else:
            speak("I do not have anything stored in my memory yet.")
            
    #Forget everything
    elif 'forget everything' in command or 'clear your memory' in command or 'clear everything' in command:
        speak("Are you sure you want me to forget everything? Say yes to confirm.")
        confirm = listen()
        if confirm and 'yes' in confirm:
            memory.clear()
            save_memory(memory)
            speak("Done. I have cleared my memory.")
        else:
            speak("Okay, I will keep my memories safe.")
    
    # Reset user profile — Nova will ask for your details again
    elif 'forget my details' in command or 'reset my profile' in command or 'forget who i am' in command:
        name       = memory.get('first_name', 'friend')
        title_word = memory.get('title', '')

        speak(f"Are you sure you want me to forget your personal details "
              f"{title_word} {name}? Say yes to confirm.")
        confirm = listen()

        if confirm and 'yes' in confirm:
            # Remove only personal details but keep appointments
            keys_to_remove = ['first_name', 'surname', 'gender',
                              'title', 'dob', 'setup_done']
            for key in keys_to_remove:
                if key in memory:
                    del memory[key]

            save_memory(memory)
            speak("Done! I have forgotten your personal details. "
                  "Please restart me and I will ask for your "
                  "information again.")
        else:
            speak("Okay! I will keep your details safe.")
    
    # Set an appointment
    elif 'record appointment' in command or 'remind me' in command or 'schedule' in command:
        name       = memory.get('first_name', 'friend')
        title_word = memory.get('title', '')

        speak(f"Of course {title_word} {name}! What is the appointment for?")
        appt_title = listen()
        if appt_title is None:
            speak("Sorry I did not catch that.")
            return

        speak("What date? Please say it like — 2025 June 15")
        date_spoken = listen()
        if date_spoken is None:
            speak("Sorry I did not catch the date.")
            return

        speak("And what time? Please say it like — 9 30 AM or 2 45 PM")
        time_spoken = listen()
        if time_spoken is None:
            speak("Sorry I did not catch the time.")
            return

        # Convert spoken date to proper format
        import datetime
        months = {
            'january': '01',   'february': '02', 'march': '03',
            'april': '04',     'may': '05',      'june': '06',
            'july': '07',      'august': '08',   'september': '09',
            'october': '10',   'november': '11', 'december': '12'
        }

        date_str = None
        for month_name, month_num in months.items():
            if month_name in date_spoken.lower():
                parts = date_spoken.lower().replace(
                    month_name, ''
                ).split()
                parts    = [p for p in parts if p.isdigit()]
                if len(parts) >= 2:
                    year     = parts[0]
                    day      = parts[1].zfill(2)
                    date_str = f"{year}-{month_num}-{day}"
                break

        if date_str is None:
            speak("Sorry I could not understand the date. Please try again.")
            return

        # Convert spoken time to proper format
        try:
            time_lower = time_spoken.lower()

            # Clean up all variations Google might return
            # Handles: 9am, 9 am, 9:00 am, 9:00 a.m, 9:00 a.m.
            time_lower = time_lower.replace('a.m.', 'am')
            time_lower = time_lower.replace('p.m.', 'pm')
            time_lower = time_lower.replace('a.m',  'am')
            time_lower = time_lower.replace('p.m',  'pm')
            time_lower = time_lower.replace(':',     ' ')
            time_lower = time_lower.replace('o\'clock', '')

            period     = 'PM' if 'pm' in time_lower else 'AM'
            time_clean = time_lower.replace('am', '').replace('pm', '').strip()
            digits     = [d for d in time_clean.split() if d.isdigit()]

            hour       = int(digits[0])
            minute     = int(digits[1]) if len(digits) > 1 else 0

            if period == 'PM' and hour != 12:
                hour += 12
            elif period == 'AM' and hour == 12:
                hour = 0

            time_str = f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
        except Exception:
            speak("Sorry I could not understand the time. Please try again.")
            return

        save_appointment(appt_title, date_str, time_str)
        speak(f"Got it {title_word} {name}! I have saved your "
              f"{appt_title} appointment. I will remind you "
              f"2 hours before, 30 minutes before, "
              f"and 5 minutes before it starts!")

    # List appointments
    elif 'can you show me my appointments' in command or 'what appointments' in command:
        if 'appointments' not in memory or not memory['appointments']:
            speak("You have no upcoming appointments saved.")
        else:
            speak(f"You have {len(memory['appointments'])} "
                  f"appointment coming up.")
            for appt in memory['appointments']:
                speak(f"{appt['title']} on {appt['date']} "
                      f"at {appt['time']}")
    
    # Find a file
    elif 'find file' in command or 'where is' in command or 'locate file' in command:
        speak("What is the name of the file you are looking for?")
        filename = listen()
        if filename:
            find_file(filename)

    # Create a folder
    elif 'create a folder' in command or 'make a folder' in command or 'new a folder' in command:
        speak("What would you like to name the folder?")
        folder_name = listen()
        if folder_name:
            create_folder(folder_name)

    # List files in a folder
    elif 'list the files' in command or 'show the files' in command or 'what is in' in command:
        speak("Which folder would you like me to look in? "
              "Say desktop, documents, downloads, "
              "pictures, music or videos.")
        folder_name = listen()
        if folder_name:
            list_files(folder_name)

    # Move a file
    elif 'move a file' in command or 'move my file' in command:
        speak("What is the name of the file you want to move?")
        filename = listen()
        if filename:
            speak("Where would you like me to move it? "
                  "Say desktop, documents, downloads, "
                  "pictures, music or videos.")
            destination = listen()
            if destination:
                move_file(filename, destination)

    # Delete a file
    elif 'delete a file' in command or 'remove a file' in command:
        speak("What is the name of the file you want to delete?")
        filename = listen()
        if filename:
            delete_file(filename)

    # Rename a file
    elif 'rename a file' in command or 'rename my file' in command:
        speak("What is the name of the file you want to rename?")
        old_name = listen()
        if old_name:
            speak("What would you like to rename it to?")
            new_name = listen()
            if new_name:
                rename_file(old_name, new_name)
    
    #Tell a joke    
    elif 'joke' in command or 'funny' in command or 'make me laugh' in command:
        setup, punchline = random.choice(JOKES)
        
        speak(setup)
        
        response = listen()
        
        if response and any(word in response for word in ['why', 'I dont know', 'no idea', 'what', 'tell me']):
            speak(punchline)
        elif response is None:
            speak("Come on bro don't be boring now. Let me tell you anyway!" + punchline)
        else:
            speak("Just say why dawg come on! Anyway..." + punchline)                                             
        
    #Who is Nova
    elif 'who are you' in command or 'your name' in command:
        speak("I am Nova, your personal voice assistance built with Python.")
        
    #Search the web
    elif 'search' in command or 'find' in command or 'look up' in command:
        speak("What would you like me to search for?")
        query = listen()
        if query:
            url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
            speak(f"Searching for {query}")
            webbrowser.open(url)
            
    #Open a website
   # elif 'open' in command:
  #      site = command.replace('open', '').strip()
   #     speak(f"Opening {site}")
   #     webbrowser.open(f"https://www.{site}.com")
        
    elif 'open' in command:
        app_name = command.replace('open', '').strip()
        
        if app_name in APPS:
            speak(f"Opening {app_name}")
            subprocess.Popen(APPS[app_name])
        else:
            speak(f"Opening {app_name}")
            webbrowser.open(f"https://www.{app_name}.com")
        
    #Shut down
    elif 'goodbye' in command or 'stop' in command or 'exit' in command:
        speak("Goodbye! Have a great day!")
        exit()
        
    #Anything Nova doesn't understand
    else:
        speak("I'm not sure about that. Let me search it for you.")
        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(command)
        webbrowser.open(url)
        
#Test commands
#speak("I am ready. Give me a command.")
#command = listen()
#if command:
#    handle_command(command)

def main():
    global memory
    calibrate_microphone()
    check_birthday()
    
    #Start appointment checker running silently in background
    reminder_thread = threading.Thread(
        target=check_appointments, daemon=False
    )
    reminder_thread.start()
    
    if not memory.get('setup_done'):
        first_time_setup()
    else:
        name       = memory.get('first_name', '')
        title_word = memory.get('title', '')
        speak(f"Welcome back {title_word} {name}! "
              f"It is great to have you back.")
        speak(f"How are you feeling today {title_word} {name}?")

        feeling = listen()
        if feeling:
            mood = detect_mood(feeling)
            if mood:
                respond_to_mood(mood)
            else:
                speak(f"That is wonderful to hear {title_word} {name}. "
                      f"Say Nova whenever you need me!")
        else:
            speak(f"No worries {title_word} {name}. "
                  f"Say Nova whenever you need me!")
    
    while True:
        print("\nWaiting for wake word 'Nova'...")
        wake = listen()
        
        if wake is None:
            continue
        
        if 'nova' in wake:
          title_word = memory.get('title', '')
          name       = memory.get('first_name', '')
          speak(f"Yes {title_word} {name}? I am listening.")
          
          #Stay awake mode - keep listening for commands until goodbye
          while True:
              command = listen()
              
              if command is None:
                  speak("I did not catch that. Try again or say goodbye to exit.")
                  continue
              
              #Check if user said goodbye BEFORE handling the command
              if 'goodbye' in command or 'stop' in command or 'exit' in command:
                  speak(f"Goodbye {title_word} {name}! Have a great day!"
                        f"I will keep watching your appointments in the background"
                        f" Say Nova whenever you need me!")
                  
                  #Switch to silent background mode
                  print("\n[Nova is running silently in the bckground]")
                  print("[Reminders are still active]")
                  print("[Say Nova to wake me up again]\n")
                  background_mode()
                  return          
              
              handle_command(command)
              
def background_mode():
    # Nova stays alive silently — only listening for her wake word
    recognizer2  = sr.Recognizer()
    microphone2  = sr.Microphone()

    recognizer2.energy_threshold      = 400
    recognizer2.dynamic_energy_threshold = False
    recognizer2.pause_threshold       = 1.0
    recognizer2.non_speaking_duration = 0.5

    print("[Background mode active — say Nova to wake up]")

    while True:
        try:
            with microphone2 as source:
                audio = recognizer2.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=5
                )
            text = recognizer2.recognize_google(audio).lower()

            if 'nova' in text:
                # Wake back up!
                title_word = memory.get('title', '')
                name       = memory.get('first_name', '')
                speak(f"I am back {title_word} {name}! "
                      f"How can I help you?")

                while True:
                    command = listen()

                    if command is None:
                        speak("I did not catch that. "
                              "Try again or say goodbye.")
                        continue

                    if any(w in command for w in
                           ['goodbye', 'stop', 'exit']):
                        speak(f"Going back to sleep "
                              f"{title_word} {name}! "
                              f"Reminders are still active.")
                        print("\n[Back to background mode]\n")
                        break

                    handle_command(command)

        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError:
            continue
        except KeyboardInterrupt:
            title_word = memory.get('title', '')
            name       = memory.get('first_name', '')
            speak(f"Shutting down completely. "
                  f"Goodbye {title_word} {name}!")
            break
#Start Nova
main()