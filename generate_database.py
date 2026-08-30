import sqlite3
import random
from datetime import datetime, timedelta

# Database connection

connection = sqlite3.connect("querygenie.db")
cursor = connection.cursor()

# Remove old tables

cursor.execute("DROP TABLE IF EXISTS order_items")
cursor.execute("DROP TABLE IF EXISTS orders")
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS customers")
cursor.execute("DROP TABLE IF EXISTS employees")
cursor.execute("DROP TABLE IF EXISTS departments")

# Create Departments table

cursor.execute("""
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT NOT NULL,
    location TEXT NOT NULL
)
""")

# Create Employees table

cursor.execute("""
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER,
    salary INTEGER,
    city TEXT,
    joining_date TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

# Create Customers table

cursor.execute("""
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    age INTEGER,
    gender TEXT
)
""")

# Create Products table

cursor.execute("""
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT,
    price INTEGER
)
""")

# Create Orders table

cursor.execute("""
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date TEXT,
    total_amount INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)
""")

# Create Order Items table

cursor.execute("""
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
)
""")

male_names = [
    "Aarav","Aditya","Nikhil","Shailesh","Rugved","Shree","Siddhesh","Pranav","Ritesh","Abhishek",
    "Viraj","Prajwal","Sanskar","Vedant","Sahil"
]

female_names = [
    "Nilam","Sanskruti","Aarya","Aradhya","Tanishka","sweety","Sreesha","Treesha","Tanvi","Preesha",
    "Samruddhi","Swati","Kavya","Gauri","Kritika"
]


last_names = [
    "Potdar", "Panchal", "Sonar", "Dixit", "Vedpathak",
    "Vedpathak", "Kulkarni", "Joshi", "Suvarnkar", "Dixit"
]

cities = [
    "Pune", "Mumbai", "Kolhapur", "Nashik",
    "Dharashiv", "Satara", "Latur", "Karad"
]

department_names = [
    "IT", "HR", "Finance", "Sales", "Marketing",
    "Operations", "Support", "Research", "Admin", "Management"
]

categories = [
    "Electronics", "Furniture", "Clothing",
    "Books", "Accessories"
]

# Inserting  Departments

for i, department in enumerate(department_names, start=1):
    location = random.choice(cities)

    cursor.execute("""
    INSERT INTO departments
    (department_id, department_name, location)
    VALUES (?, ?, ?)
    """, (i, department, location))

# Insert Employees

for i in range(1, 201):
    gender = random.choice(["Male", "Female"])

    if gender == "Male":
        first_name = random.choice(male_names)
    else:
        first_name = random.choice(female_names)    

    name = first_name + " " + random.choice(last_names)
    department_id = random.randint(1, 10)
    salary = random.randint(25000, 100000)
    city = random.choice(cities)

    start_date = datetime(2018, 1, 1)
    random_days = random.randint(0, 2500)

    joining_date = (
        start_date + timedelta(days=random_days)
    ).strftime("%Y-%m-%d")

    cursor.execute("""
    INSERT INTO employees
    (employee_id, name, department_id, salary, city, joining_date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        i,
        name,
        department_id,
        salary,
        city,
        joining_date
    ))

# Insert Customers

for i in range(1, 301):

    # Choose gender first
    gender = random.choice(["Male", "Female"])

    # Choose matching first name
    if gender == "Male":
        first_name = random.choice(male_names)
    else:
        first_name = random.choice(female_names)

    # Choose surname
    last_name = random.choice(last_names)

    # Create full name
    name = first_name + " " + last_name

    # Other customer details
    city = random.choice(cities)

    age = random.randint(18, 65)

    # Insert customer
    cursor.execute("""
        INSERT INTO customers
        (customer_id, name, city, age, gender)
        VALUES (?, ?, ?, ?, ?)
    """, (
        i,
        name,
        city,
        age,
        gender
    ))

# Inserting  Products

product_names = [
    "Laptop", "Smartphone", "Tablet", "Headphones",
    "Keyboard", "Mouse", "Monitor", "Printer",
    "Desk", "Chair", "Backpack", "Shoes",
    "T-Shirt", "Book", "Smart Watch"
]

for i in range(1, 101):

    product_name = random.choice(product_names) + f" {i}"

    category = random.choice(categories)

    price = random.randint(500, 100000)

    cursor.execute("""
    INSERT INTO products
    (product_id, product_name, category, price)
    VALUES (?, ?, ?, ?)
    """, (
        i,
        product_name,
        category,
        price
    ))

# Inserting  Orders

for i in range(1, 251):

    customer_id = random.randint(1, 300)

    start_date = datetime(2024, 1, 1)

    random_days = random.randint(0, 730)

    order_date = (
        start_date + timedelta(days=random_days)
    ).strftime("%Y-%m-%d")

    total_amount = random.randint(500, 100000)

    cursor.execute("""
    INSERT INTO orders
    (order_id, customer_id, order_date, total_amount)
    VALUES (?, ?, ?, ?)
    """, (
        i,
        customer_id,
        order_date,
        total_amount
    ))

# Insert Order Items

for i in range(1, 141):

    order_id = random.randint(1, 250)

    product_id = random.randint(1, 100)

    quantity = random.randint(1, 5)

    cursor.execute("""
    INSERT INTO order_items
    (order_item_id, order_id, product_id, quantity)
    VALUES (?, ?, ?, ?)
    """, (
        i,
        order_id,
        product_id,
        quantity
    ))

# Save database
connection.commit()
connection.close()

print("===================================")
print("QueryGenie database created!")
print("===================================")
print("Departments : 10")
print("Employees   : 200")
print("Customers   : 300")
print("Products    : 100")
print("Orders      : 250")
print("Order Items : 140")
print("===================================")
print("Total records: 1000")
print("===================================")