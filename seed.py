"""Creates the sample e-commerce database (5 related tables). Run once: python seed.py"""
import random
from datetime import date, timedelta
from sqlalchemy import (MetaData, Table, Column, Integer, String, Numeric,
                        Date, ForeignKey)
from db import engine

meta = MetaData()

customers = Table("customers", meta,
    Column("customer_id", Integer, primary_key=True),
    Column("name", String(50)),
    Column("city", String(50)))

categories = Table("categories", meta,
    Column("category_id", Integer, primary_key=True),
    Column("category_name", String(50)))

products = Table("products", meta,
    Column("product_id", Integer, primary_key=True),
    Column("product_name", String(50)),
    Column("price", Numeric(10, 2)),
    Column("category_id", ForeignKey("categories.category_id")))

orders = Table("orders", meta,
    Column("order_id", Integer, primary_key=True),
    Column("customer_id", ForeignKey("customers.customer_id")),
    Column("order_date", Date))

order_items = Table("order_items", meta,
    Column("item_id", Integer, primary_key=True),
    Column("order_id", ForeignKey("orders.order_id")),
    Column("product_id", ForeignKey("products.product_id")),
    Column("quantity", Integer))

if __name__ == "__main__":
    meta.drop_all(engine)
    meta.create_all(engine)
    random.seed(1)

    cust = [("Rahul", "Pune"), ("Amit", "Mumbai"), ("Sneha", "Pune"),
            ("Priya", "Nagpur"), ("Vikram", "Delhi"), ("Anjali", "Mumbai")]
    cats = ["Electronics", "Accessories", "Home"]
    prods = [("Laptop", 50000, 1), ("Mobile", 20000, 1), ("Headphones", 2000, 2),
             ("Keyboard", 1500, 2), ("Mixer", 3500, 3), ("Lamp", 800, 3)]

    with engine.begin() as c:
        c.execute(customers.insert(), [
            {"customer_id": i + 1, "name": n, "city": ct} for i, (n, ct) in enumerate(cust)])
        c.execute(categories.insert(), [
            {"category_id": i + 1, "category_name": n} for i, n in enumerate(cats)])
        c.execute(products.insert(), [
            {"product_id": i + 1, "product_name": n, "price": p, "category_id": k}
            for i, (n, p, k) in enumerate(prods)])
        # 30 random orders, 1-3 items each
        item_id = 1
        for oid in range(1, 31):
            c.execute(orders.insert(), {
                "order_id": oid,
                "customer_id": random.randint(1, len(cust)),
                "order_date": date(2026, 1, 1) + timedelta(days=random.randint(0, 300))})
            for pid in random.sample(range(1, len(prods) + 1), random.randint(1, 3)):
                c.execute(order_items.insert(), {
                    "item_id": item_id, "order_id": oid,
                    "product_id": pid, "quantity": random.randint(1, 4)})
                item_id += 1
    print("Database seeded.")
