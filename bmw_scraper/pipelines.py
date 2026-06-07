import sqlite3
from datetime import datetime

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class SqlitePipeline:
    def open_spider(self, spider):
        self.conn = sqlite3.connect("bmw_cars.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT,
                name TEXT,
                mileage INTEGER,
                registered TEXT,
                engine INTEGER,
                range_ INTEGER,
                exterior TEXT,
                fuel TEXT,
                transmission TEXT,
                registration TEXT UNIQUE,
                upholstery TEXT
            )
        """)
        self.conn.commit()

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        try:
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO cars
                (model, name, mileage, registered, engine, range_, exterior, fuel, transmission, registration, upholstery)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    adapter.get("model"),
                    adapter.get("name"),
                    adapter.get("mileage"),
                    adapter.get("registered"),
                    adapter.get("engine"),
                    adapter.get("range_"),
                    adapter.get("exterior"),
                    adapter.get("fuel"),
                    adapter.get("transmission"),
                    adapter.get("registration"),
                    adapter.get("upholstery"),
                ),
            )
            self.conn.commit()
        except Exception as e:
            spider.logger.error(f"DB error: {e}")
        return item


class ValidationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field in ["model", "name", "registration"]:
            if not adapter.get(field):
                spider.logger.warning(f"Dropping item: missing field '{field}': {item}")
                raise DropItem(f"Missing required field: {field}")

        mileage = adapter.get("mileage")
        if mileage is not None:
            if isinstance(mileage, str):
                mileage = int(mileage.replace(",", ""))
            adapter["mileage"] = int(mileage)

        registered = adapter.get("registered")
        if registered:
            try:
                dt = datetime.strptime(registered, "%Y-%m-%dT%H:%M:%SZ")
                adapter["registered"] = dt.strftime("%b %Y")
            except ValueError:
                pass

        fuel = adapter.get("fuel")
        if fuel:
            adapter["fuel"] = fuel.lower()

        return item
