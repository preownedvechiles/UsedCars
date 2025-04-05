import streamlit as st
import pandas as pd
import sqlite3
import os
import smtplib
import random
import bcrypt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image

# Ensure 'images' directory exists
image_dir = "images"
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Database connection
def connect_db():
    return sqlite3.connect("used_cars.db", check_same_thread=False)

# Initialize database
def init_db():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cars (
                            id INTEGER PRIMARY KEY,
                            make TEXT,
                            model TEXT,
                            year INTEGER,
                            fuel TEXT,
                            kilometers TEXT,
                            owners TEXT,
                            color TEXT,
                            price REAL,
                            image_paths TEXT,
                            contact TEXT,
                            state TEXT,
                            city TEXT,
                            pincode TEXT,
                            features TEXT,
                            email TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            email TEXT UNIQUE,
                            username TEXT UNIQUE,
                            password TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS otp_storage (
                            email TEXT PRIMARY KEY,
                            otp TEXT)''')
        conn.commit()

# Initialize DB
init_db()

st.set_page_config(layout="wide")
st.title("\U0001F697 India's Used Car Marketplace")

# Ensure session state variables exist
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = ""

# Gmail credentials (replace with actual credentials)
SENDER_EMAIL = "usedcars.pov@gmail.com"
SENDER_PASSWORD = "aadswmtcfkyvsfuq"

# Function to send OTP
def send_otp(email):
    otp = str(random.randint(100000, 999999))
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO otp_storage (email, otp) VALUES (?, ?)", (email, otp))
        conn.commit()
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg['Subject'] = "Your OTP Code"
    msg.attach(MIMEText(f"Your OTP is {otp}.  For any queries with the website, Please feel free to 📞 Contact us at: +91 8660356670 or ✉️ Email us at usedcars.pov@gmail.com", 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error sending OTP: {e}")
        return False

# Function to authenticate OTP
def authenticate(email, otp):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT otp FROM otp_storage WHERE email=?", (email,))
        stored_otp = cursor.fetchone()
        if stored_otp and stored_otp[0] == otp:
            return True
    return False

# Load dynamic dropdown values
makes =  {
    "Maruti Suzuki": ["Alto", "Swift", "Baleno", "Wagon R", "Dzire", "Ertiga", "Brezza", "Ciaz"],
    "Hyundai": ["Santro", "i10", "i20", "Creta", "Venue", "Verna", "Tucson"],
    "Tata": ["Nano", "Tiago", "Tigor", "Altroz", "Harrier", "Safari", "Nexon", "Punch"],
    "Mahindra": ["Bolero", "Thar", "Scorpio", "XUV300", "XUV500", "XUV700"],
    "Honda": ["City", "Amaze", "Jazz", "WR-V", "CR-V"],
    "Toyota": ["Innova", "Fortuner", "Glanza", "Camry", "Urban Cruiser"],
    "Ford": ["EcoSport", "Endeavour", "Figo", "Aspire"],
    "Renault": ["Kwid", "Triber", "Duster", "Kiger"],
    "Nissan": ["Magnite", "Kicks", "Sunny"],
    "Volkswagen": ["Polo", "Vento", "Taigun", "Tiguan"],
    "Skoda": ["Rapid", "Octavia", "Superb", "Kushaq", "Slavia"],
    "Kia": ["Seltos", "Sonet", "Carens", "EV6"],
    "MG": ["Hector", "Astor", "Gloster", "ZS EV"],
    "Jeep": ["Compass", "Meridian", "Wrangler", "Grand Cherokee"],
    "Mercedes-Benz": ["A-Class", "C-Class", "E-Class", "GLA", "GLE"],
    "BMW": ["3 Series", "5 Series", "X1", "X3", "X5"],
    "Audi": ["A4", "A6", "Q3", "Q5", "Q7"],
    "Lexus": ["ES", "RX", "NX", "LX"],
    "Jaguar": ["XE", "XF", "F-Pace"],
    "Land Rover": ["Defender", "Discovery", "Range Rover Evoque"],
}

states = states = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati", "Kakinada", "Rajahmundry"],
    "Arunachal Pradesh": ["Itanagar", "Naharlagun", "Pasighat", "Tawang", "Ziro", "Bomdila"],
    "Assam": ["Guwahati", "Dibrugarh", "Silchar", "Jorhat", "Tezpur", "Nagaon"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga", "Purnia", "Begusarai"],
    "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba", "Durg", "Rajnandgaon", "Jagdalpur"],
    "Goa": ["Panaji", "Margao", "Vasco da Gama", "Mapusa", "Ponda", "Bicholim"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Gandhinagar"],
    "Haryana": ["Gurgaon", "Faridabad", "Panipat", "Ambala", "Karnal", "Rohtak", "Hisar"],
    "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala", "Kullu", "Mandi", "Solan", "Bilaspur"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Hazaribagh", "Deoghar"],
    "Karnataka": ["Bellary","Bengaluru", "Mysuru", "Mangalore", "Hubli", "Belgaum", "Davanagere", "Tumkur"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Alappuzha", "Kollam", "Kannur"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain", "Sagar", "Satna"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Solapur", "Amravati"],
    "Manipur": ["Imphal", "Thoubal", "Bishnupur", "Churachandpur", "Ukhrul", "Senapati"],
    "Meghalaya": ["Shillong", "Tura", "Jowai", "Nongstoin", "Baghmara", "Williamnagar"],
    "Mizoram": ["Aizawl", "Lunglei", "Saiha", "Champhai", "Serchhip", "Kolasib"],
    "Nagaland": ["Kohima", "Dimapur", "Mokokchung", "Tuensang", "Wokha", "Zunheboto"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Berhampur", "Sambalpur", "Balasore", "Puri"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Pathankot", "Hoshiarpur"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer", "Alwar"],
    "Sikkim": ["Gangtok", "Namchi", "Mangan", "Rangpo", "Gyalshing", "Pelling"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Erode", "Vellore"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam", "Ramagundam"],
    "Tripura": ["Agartala", "Udaipur", "Dharmanagar", "Kailashahar", "Ambassa", "Belonia"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Meerut", "Allahabad", "Bareilly"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Rishikesh", "Nainital", "Haldwani", "Rudrapur", "Almora"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Siliguri", "Asansol", "Malda", "Kharagpur"]
}


kilometers_options = ["0-10,000", "10,000-50,000", "50,000-100,000", "100,000+"]
owners_options = ["1", "2", "3+"]
features_options = [
    "Sunroof", "Leather Seats", "Bluetooth", "Backup Camera", "Navigation System",
    "Wireless Charging", "Adaptive Cruise Control", "Blind Spot Monitoring",
    "Lane Keep Assist", "Automatic Emergency Braking", "360-Degree Camera",
    "Ventilated Seats", "Heads-Up Display", "Apple CarPlay", "Android Auto",
    "Heated Seats", "Cooled Seats", "Keyless Entry", "Push Button Start",
    "Digital Instrument Cluster", "Automatic Climate Control", "Ambient Lighting",
    "Rear Parking Sensors", "Front Parking Sensors", "Voice Control",
    "Remote Engine Start", "Auto-Dimming Rearview Mirror", "Rain Sensing Wipers",
    "Electric Tailgate", "AI-Based Driver Assistance", "Gesture Control"
]


# Sidebar Filter Panel (Always visible)
with st.sidebar:
    st.header("\U0001F50D Filter Cars")
    selected_make = st.selectbox("Make", ["All"] + list(makes.keys()))
    selected_model = st.selectbox("Model", ["All"] + makes.get(selected_make, []))
    selected_fuel = st.selectbox("Fuel", ["All", "Petrol", "Diesel", "EV"])
    selected_kilometers = st.selectbox("Kilometers Driven", ["All"] + kilometers_options)
    selected_owners = st.selectbox("Number of Owners", ["All"] + owners_options)
    selected_state = st.selectbox("State", ["All"] + list(states.keys()))
    selected_city = st.selectbox("City", ["All"] + states.get(selected_state, []))

# Sidebar Login Panel
st.info("📞 For any queries with the website, Contact us at: **+91 8660356670** or ✉️ Email us at **[usedcars.pov@gmail.com](mailto:usedcars.pov@gmail.com)**")

with st.sidebar:
    if not st.session_state.logged_in:
        st.header("\U0001F511 Login")
        email = st.text_input("Enter your email")
        if st.button("Send OTP"):
            if send_otp(email):
                st.success("OTP sent successfully!")
        otp = st.text_input("Enter OTP", type="password")
        if st.button("Login"):
            if authenticate(email, otp):
                st.session_state.logged_in = True
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Invalid OTP")
    else:
        st.write(f"Logged in as: {st.session_state.email}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.email = ""
            st.rerun()

# Add Car Form (Visible only if logged in)
if st.session_state.logged_in:
    with st.expander("\U0001F4DD Add Your Car", expanded=False):
        with st.form("add_car_form"):
            make = st.selectbox("Make", list(makes.keys()))
            model = st.selectbox("Model", makes.get(make, []))
            year = st.number_input("Year", min_value=1990, max_value=2025, step=1)
            fuel = st.selectbox("Fuel", ["Petrol", "Diesel", "EV"])
            kilometers = st.selectbox("Kilometers Driven", kilometers_options)
            owners = st.selectbox("Number of Owners", owners_options)
            color = st.text_input("Color")
            price = st.number_input("Price", min_value=0, step=1000)
            state = st.selectbox("State", list(states.keys()))
            city = st.selectbox("City", states.get(state, []))
            features = st.multiselect("Features", features_options)
            contact = st.text_input("Contact Number")
            images = st.file_uploader("Upload Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

            # Ensure this line is inside the form block
            submitted = st.form_submit_button("Add Car")

            if submitted:
                if not contact.isdigit() or len(contact) != 10:
                    st.error("Please enter a valid 10-digit mobile number.")
                else:
                    image_paths = []
                    for image in images:
                        image_path = os.path.join(image_dir, image.name)
                        with open(image_path, "wb") as f:
                            f.write(image.getbuffer())
                        image_paths.append(image_path)
                    
                    with connect_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """INSERT INTO cars (make, model, year, fuel, kilometers, owners, color, price, 
                            state, city, contact, features, email, image_paths) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (make, model, year, fuel, kilometers, owners, color, price, state, city, 
                            contact, ",".join(features), st.session_state.email, ",".join(image_paths))
                        )
                        conn.commit()
                        st.success("Car added successfully!")
                        st.rerun()





# Display user's posts in a separate tab
if st.session_state.logged_in:
    st.header("Your Posts")
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, make, model, price, image_paths FROM cars WHERE email=?", (st.session_state.email,))
        user_cars = cursor.fetchall()
    
    if user_cars:
        for car_id, make, model, price, image_paths in user_cars:
            with st.expander(f"{make} {model} - ₹{price}"):
                if image_paths:
                    st.image(image_paths.split(",")[:5], width=150)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit", key=f"edit_{car_id}"):
                        st.session_state.editing_car_id = car_id
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"delete_{car_id}"):
                        with connect_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM cars WHERE id=?", (car_id,))
                            conn.commit()
                        st.success("Post deleted successfully!")
                        st.rerun()
# Display Car Listings
st.header("\U0001F4C8 Car Listings")
filter_query = "SELECT * FROM cars WHERE 1=1"
params = []
if selected_make != "All":
    filter_query += " AND make=?"
    params.append(selected_make)
if selected_model != "All":
    filter_query += " AND model=?"
    params.append(selected_model)
with connect_db() as conn:
    cars_df = pd.read_sql_query(filter_query, conn, params=params)
    for _, row in cars_df.iterrows():
        st.subheader(f"{row['make']} {row['model']} ({row['year']})")
    
        st.markdown(f"""
**Fuel:** {row['fuel']}  
**Features:** {', '.join(row["features"].split(","))}  
**Kilometers:** {row['kilometers']}  
**Owners:** {row['owners']}  
**Color:** {row['color']}  
**State:** {row['state']} **City:** {row['city']}  
**Price:** ₹{row['price']}""", unsafe_allow_html=True)


      

       # Display Multiple Images Horizontally
        if row["image_paths"]:
            image_list = row["image_paths"].split(",")  # Split string into list of paths
            image_list = [img.strip() for img in image_list if os.path.exists(img.strip())]  # Validate images

            if image_list:
                cols = st.columns(len(image_list))  # Create dynamic columns
                for col, image_path in zip(cols, image_list):
                    with col:
                        st.image(image_path, width=250)

        # Display Contact Info
        st.markdown(f"📞 **Contact at**: {row['contact']} or ✉️ **Email:** {row['email']}")

