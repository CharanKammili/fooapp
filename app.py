import pandas as pd

# Load the datasets
providers_df = pd.read_csv('providers_data.csv')
receivers_df = pd.read_csv('receivers_data.csv')
food_listings_df = pd.read_csv('food_listings_data.csv')
claims_df = pd.read_csv('claims_data.csv')

# You can perform initial cleaning and checks here if needed
print("Providers Data:")
print(providers_df.head())
print("\nReceivers Data:")
print(receivers_df.head())
print("\nFood Listings Data:")
print(food_listings_df.head())
print("\nClaims Data:")
print(claims_df.head())

import sqlite3
import pandas as pd

# Connect to SQLite database (or create if it doesn't exist)
database_name = 'food_wastage.db'
connection = sqlite3.connect(database_name)
cursor = connection.cursor()

# Create Providers table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Providers (
        Provider_ID INTEGER PRIMARY KEY,
        Name TEXT,
        Type TEXT,
        Address TEXT,
        City TEXT,
        Contact TEXT
    )
''')

# Create Receivers table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Receivers (
        Receiver_ID INTEGER PRIMARY KEY,
        Name TEXT,
        Type TEXT,
        City TEXT,
        Contact TEXT
    )
''')

# Create Food Listings table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS FoodListings (
        Food_ID INTEGER PRIMARY KEY,
        Food_Name TEXT,
        Quantity INTEGER,
        Expiry_Date DATE,
        Provider_ID INTEGER,
        Provider_Type TEXT,
        Location TEXT,
        Food_Type TEXT,
        Meal_Type TEXT
    )
''')

# Create Claims table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Claims (
        Claim_ID INTEGER PRIMARY KEY,
        Food_ID INTEGER,
        Receiver_ID INTEGER,
        Status TEXT,
        Timestamp DATETIME
    )
''')

connection.commit()
print(f"Database '{database_name}' and tables created successfully!")

# Insert data into Providers table
providers_df.to_sql('Providers', connection, if_exists='replace', index=False)

# Insert data into Receivers table
receivers_df.to_sql('Receivers', connection, if_exists='replace', index=False)

# Insert data into FoodListings table
food_listings_df['Expiry_Date'] = pd.to_datetime(food_listings_df['Expiry_Date']).dt.strftime('%Y-%m-%d') # Format date for SQLite
food_listings_df.to_sql('FoodListings', connection, if_exists='replace', index=False)

# Insert data into Claims table
claims_df['Timestamp'] = pd.to_datetime(claims_df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S') # Format datetime for SQLite
claims_df.to_sql('Claims', connection, if_exists='replace', index=False)

print("Data inserted into tables successfully!")

# Close the connection
connection.close()


import sqlite3
import pandas as pd

database_name = 'food_wastage.db'
connection = sqlite3.connect(database_name)
cursor = connection.cursor()

queries = [
    ("How many food providers and receivers are there in each city?",
     "SELECT City, COUNT(Provider_ID) AS ProviderCount, (SELECT COUNT(Receiver_ID) FROM Receivers WHERE City = p.City) AS ReceiverCount FROM Providers p GROUP BY City;"),
    ("Which type of food provider (restaurant, grocery store, etc.) contributes the most food (based on number of listings)?",
     "SELECT Provider_Type, COUNT(Food_ID) AS ListingCount FROM FoodListings GROUP BY Provider_Type ORDER BY ListingCount DESC LIMIT 1;"),
    ("What is the contact information of food providers in a specific city? (e.g., 'New York')",
     "SELECT Name, Contact FROM Providers WHERE City = 'New York';"),
    ("Which receivers have claimed the most food (based on number of claims)?",
     "SELECT r.Name, COUNT(c.Claim_ID) AS ClaimCount FROM Claims c JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID GROUP BY r.Receiver_ID ORDER BY ClaimCount DESC LIMIT 5;"),
    ("What is the total quantity of food available from all providers?",
     "SELECT SUM(Quantity) AS TotalQuantity FROM FoodListings;"),
    ("Which city has the highest number of food listings?",
     "SELECT Location, COUNT(Food_ID) AS ListingCount FROM FoodListings GROUP BY Location ORDER BY ListingCount DESC LIMIT 1;"),
    ("What are the most commonly available food types (top 5)?",
     "SELECT Food_Type, COUNT(Food_ID) AS Count FROM FoodListings GROUP BY Food_Type ORDER BY Count DESC LIMIT 5;"),
    ("Which food listings are expiring soon (within the next 3 days)?",
     "SELECT Food_Name, Expiry_Date FROM FoodListings WHERE Expiry_Date BETWEEN DATE('now') AND DATE('now', '+3 days');"),
    ("How many food claims have been made for each food item?",
     "SELECT fl.Food_Name, COUNT(c.Claim_ID) AS ClaimCount FROM Claims c JOIN FoodListings fl ON c.Food_ID = fl.Food_ID GROUP BY c.Food_ID ORDER BY ClaimCount DESC;"),
    ("Which provider has had the highest number of successful food claims? (assuming 'Completed' status for successful claims)",
     "SELECT p.Name, COUNT(c.Claim_ID) AS SuccessfulClaims FROM Claims c JOIN FoodListings fl ON c.Food_ID = fl.Food_ID JOIN Providers p ON fl.Provider_ID = p.Provider_ID WHERE c.Status = 'Completed' GROUP BY p.Provider_ID ORDER BY SuccessfulClaims DESC LIMIT 1;"),
    ("Which city has the fastest claim rate (measured by the number of claims)?",
     "SELECT fl.Location, COUNT(c.Claim_ID) AS ClaimCount FROM Claims c JOIN FoodListings fl ON c.Food_ID = fl.Food_ID GROUP BY fl.Location ORDER BY ClaimCount DESC LIMIT 1;"),
    ("What percentage of food claims are completed vs. pending vs. canceled?",
     "SELECT Status, (CAST(COUNT(Claim_ID) AS REAL) * 100 / (SELECT COUNT(Claim_ID) FROM Claims)) AS Percentage FROM Claims GROUP BY Status;"),
    ("What is the average quantity of food claimed per receiver?",
     """SELECT r.Name, AVG(fl.Quantity) AS AverageClaimedQuantity
        FROM Claims c
        JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
        JOIN FoodListings fl ON c.Food_ID = fl.Food_ID
        GROUP BY r.Receiver_ID;"""),
    ("Which meal type (breakfast, lunch, dinner, snacks) is claimed the most?",
     "SELECT fl.Meal_Type, COUNT(c.Claim_ID) AS ClaimCount FROM Claims c JOIN FoodListings fl ON c.Food_ID = fl.Food_ID GROUP BY fl.Meal_Type ORDER BY ClaimCount DESC LIMIT 1;"),
    ("What is the total quantity of food donated by each provider?",
     "SELECT p.Name, SUM(fl.Quantity) AS TotalDonatedQuantity FROM FoodListings fl JOIN Providers p ON fl.Provider_ID = p.Provider_ID GROUP BY p.Provider_ID;")
]

for question, query in queries:
    print(f"\nQuestion: {question}")
    try:
        df = pd.read_sql_query(query, connection)
        print(df)
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")

connection.close()


import streamlit as st
import pandas as pd
import sqlite3

# Database connection function
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        st.error(f"Database Error: {e}")
    return conn

# Function to execute SQL query and return as DataFrame
def execute_query(conn, query):
    try:
        return pd.read_sql_query(query, conn)
    except sqlite3.Error as e:
        st.error(f"Query Error: {e}")
        return pd.DataFrame()

def main():
    st.title("Local Food Wastage Management System")

    db_file = 'food_wastage.db'
    conn = create_connection(db_file)

    if conn:
        st.subheader("Food Donation Listings")

        # --- Filtering Options ---
        st.sidebar.header("Filter Donations")
        cities_df = execute_query(conn, "SELECT DISTINCT Location FROM FoodListings")
        cities = cities_df['Location'].tolist() if not cities_df.empty else []
        city_filter = st.sidebar.multiselect("Filter by City", cities)

        provider_types_df = execute_query(conn, "SELECT DISTINCT Provider_Type FROM FoodListings")
        provider_types = provider_types_df['Provider_Type'].tolist() if not provider_types_df.empty else []
        provider_filter = st.sidebar.multiselect("Filter by Provider Type", provider_types)

        food_types_df = execute_query(conn, "SELECT DISTINCT Food_Type FROM FoodListings")
        food_types = food_types_df['Food_Type'].tolist() if not food_types_df.empty else []
        food_type_filter = st.sidebar.multiselect("Filter by Food Type", food_types)

        meal_types_df = execute_query(conn, "SELECT DISTINCT Meal_Type FROM FoodListings")
        meal_types = meal_types_df['Meal_Type'].tolist() if not meal_types_df.empty else []
        meal_type_filter = st.sidebar.multiselect("Filter by Meal Type", meal_types)

        query = "SELECT * FROM FoodListings"
        conditions = []
        if city_filter:
            conditions.append(f"Location IN ('" + "', '".join(map(str, city_filter)) + "')")
        if provider_filter:
            conditions.append(f"Provider_Type IN ('" + "', '".join(map(str, provider_filter)) + "')")
        if food_type_filter:
            conditions.append(f"Food_Type IN ('" + "', '".join(map(str, food_type_filter)) + "')")
        if meal_type_filter:
            conditions.append(f"Meal_Type IN ('" + "', '".join(map(str, meal_type_filter)) + "')")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        food_listings_df = execute_query(conn, query)
        st.dataframe(food_listings_df)

        st.subheader("Contact Food Providers")
        food_ids_df = execute_query(conn, "SELECT Food_ID FROM FoodListings")
        food_ids = food_ids_df['Food_ID'].tolist() if not food_ids_df.empty else []
        selected_food_id = st.selectbox("Select a Food Item to see Provider Contact", food_ids)
        if selected_food_id:
            provider_info_query = f"""
                SELECT p.Name AS ProviderName, p.Contact
                FROM Providers p
                JOIN FoodListings fl ON p.Provider_ID = fl.Provider_ID
                WHERE fl.Food_ID = {selected_food_id}
            """
            provider_info_df = execute_query(conn, provider_info_query)
            if not provider_info_df.empty:
                st.write(f"**Provider Name:** {provider_info_df['ProviderName'].iloc[0]}")
                st.write(f"**Contact:** {provider_info_df['Contact'].iloc[0]}")
            else:
                st.warning("Provider information not found for this food item.")

        st.subheader("SQL Query Outputs")
        queries = [
            ("How many food providers and receivers are there in each city?",
             "SELECT City, COUNT(Provider_ID) AS ProviderCount, (SELECT COUNT(Receiver_ID) FROM Receivers WHERE City = p.City) AS ReceiverCount FROM Providers p GROUP BY City;"),
            ("Which type of food provider (restaurant, grocery store, etc.) contributes the most food (based on number of listings)?",
             "SELECT Provider_Type, COUNT(Food_ID) AS ListingCount FROM FoodListings GROUP BY Provider_Type ORDER BY ListingCount DESC LIMIT 1;"),
            ("What is the contact information of food providers in a specific city? (e.g., 'New York')",
             "SELECT Name, Contact FROM Providers WHERE City = 'New York';"),
            ("Which receivers have claimed the most food (based on number of claims)?",
             "SELECT r.Name, COUNT(c.Claim_ID) AS ClaimCount FROM Claims c JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID GROUP BY r.Receiver_ID ORDER BY ClaimCount DESC LIMIT 5;"),
            ("What is the total quantity of food available from all providers?",
             "SELECT SUM(Quantity) AS TotalQuantity FROM FoodListings;"),
            ("Which city has the highest number of food listings?",
             "SELECT Location, COUNT(Food_ID) AS ListingCount FROM FoodListings GROUP BY Location ORDER BY ListingCount DESC LIMIT 1;"),
            ("What are the most commonly available food types (top 5)?",
             "SELECT Food_Type, COUNT(Food_ID) AS Count FROM FoodListings GROUP BY Food_Type ORDER BY Count DESC LIMIT 5;"),
            ("Which food listings are expiring soon (within the next 3 days)?",
             "SELECT Food_Name, Expiry_Date FROM FoodListings WHERE Expiry_Date BETWEEN DATE('now') AND DATE('now', '+3 days');"),
            ("How many food claims have been made for each food item?",
             "SELECT fl.Food_Name, COUNT(c.Claim_ID) AS ClaimCount FROM Claims c JOIN FoodListings fl ON c.Food_ID = fl.Food_ID GROUP BY c.Food_ID ORDER BY ClaimCount DESC;"),
            ("Which provider has had the highest number of successful food claims? (assuming 'Completed' status for successful claims)",
             "SELECT p.Name, COUNT(c.Claim_ID) AS SuccessfulClaims FROM Claims c JOIN FoodListings fl ON c.Food_ID = fl.Food_ID JOIN Providers p ON fl.Provider_ID = p.Provider_ID WHERE c.Status = 'Completed' GROUP BY p.Provider_ID ORDER BY SuccessfulClaims DESC LIMIT 1;"),
            ("Which city has the fastest claim rate (measured by the number of claims)?",
             "SELECT fl.Location, COUNT(c.Claim_ID) AS ClaimCount FROM Claims c JOIN FoodListings fl ON c.Food_ID = fl.Food_ID GROUP BY fl.Location ORDER BY ClaimCount DESC LIMIT 1;"),
            ("What percentage of food claims are completed vs. pending vs. canceled?",
             "SELECT Status, (CAST(COUNT(Claim_ID) AS REAL) * 100 / (SELECT COUNT(Claim_ID) FROM Claims)) AS Percentage FROM Claims GROUP BY Status;"),
            ("What is the average quantity of food claimed per receiver?",
             """SELECT r.Name, AVG(fl.Quantity) AS AverageClaimedQuantity
                FROM Claims c
                JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
                JOIN FoodListings fl ON c.Food_ID = fl.Food_ID
                GROUP BY r.Receiver_ID;"""),
            ("Which meal type (breakfast, lunch, dinner, snacks) is claimed the most?",
             "SELECT fl.Meal_Type, COUNT(c.Claim_ID) AS ClaimCount FROM Claims c JOIN FoodListings fl ON c.Food_ID = fl.Food_ID GROUP BY fl.Meal_Type ORDER BY ClaimCount DESC LIMIT 1;"),
            ("What is the total quantity of food donated by each provider?",
             "SELECT p.Name, SUM(fl.Quantity) AS TotalDonatedQuantity FROM FoodListings fl JOIN Providers p ON fl.Provider_ID = p.Provider_ID GROUP BY p.Provider_ID;")
        ]
        for i, (question, sql_query) in enumerate(queries):
            st.markdown(f"**Query {i+1}:** {question}")
            result_df = execute_query(conn, sql_query)
            st.dataframe(result_df)

        conn.close()

if __name__ == "__main__":
    main()

