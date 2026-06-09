import psycopg2
import requests
from dotenv import load_dotenv, find_dotenv
import os
import random
from datetime import datetime, timedelta

load_dotenv(find_dotenv())

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(50),
    signup_date DATE
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10,2),
    stock INTEGER
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date DATE,
    status VARCHAR(20),
    total_amount DECIMAL(10,2)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER,
    unit_price DECIMAL(10,2)
);
""")

print("Fetching data from FakeStoreAPI...")

# Fetch users
users_res = requests.get("https://fakestoreapi.com/users")
users = users_res.json()

for user in users:
    name = user["name"]["firstname"] + " " + user["name"]["lastname"]
    email = user["email"]
    city = user["address"]["city"]
    signup = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
    cur.execute(
        "INSERT INTO customers (name, email, city, signup_date) VALUES (%s, %s, %s, %s)",
        (name, email, city, signup)
    )

print(f"Inserted {len(users)} customers")

# Fetch products
products_res = requests.get("https://fakestoreapi.com/products")
products = products_res.json()

for product in products:
    name = product["title"][:100]
    category = product["category"][:50]
    price = round(product["price"], 2)
    stock = random.randint(10, 200)
    cur.execute(
        "INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)",
        (name, category, price, stock)
    )

print(f"Inserted {len(products)} products")

# Fetch carts for orders
carts_res = requests.get("https://fakestoreapi.com/carts")
carts = carts_res.json()

statuses = ["delivered", "pending", "cancelled", "shipped"]

for cart in carts:
    customer_id = cart["userId"]
    order_date = datetime.strptime(cart["date"], "%Y-%m-%dT%H:%M:%S.%fZ").date()
    status = random.choice(statuses)

    # Calculate total from cart items
    total = 0
    for item in cart["products"]:
        product_id = item["productId"]
        quantity = item["quantity"]
        # Get product price
        cur.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        row = cur.fetchone()
        if row:
            total += row[0] * quantity

    cur.execute(
        "INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES (%s, %s, %s, %s) RETURNING id",
        (customer_id, order_date, status, round(total, 2))
    )
    order_id = cur.fetchone()[0]

    # Insert order items
    for item in cart["products"]:
        product_id = item["productId"]
        quantity = item["quantity"]
        cur.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                (order_id, product_id, quantity, row[0])
            )

print(f"Inserted {len(carts)} orders with items")

conn.commit()
cur.close()
conn.close()
print("Done! Database populated from FakeStoreAPI.")