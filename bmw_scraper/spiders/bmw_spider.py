import json
import re

import scrapy

from bmw_scraper.items import BmwScraperItem


class BmwSpider(scrapy.Spider):
    name = "bmw"

    async def start(self):
        yield scrapy.Request(
            "https://usedcars.bmw.co.uk/result/?payment_type=cash&size=23&source=home",
            callback=self.parse_home,
        )

    def parse_home(self, response):

        cookies = response.headers.getlist("Set-Cookie")
        csrf = ""
        for c in cookies:
            c = c.decode()
            match = re.search(r"csrftoken=([^;]+)", c)
            if match:
                csrf = match.group(1)
                break

        base = "https://usedcars.bmw.co.uk/vehicle/api/list/?payment_type=cash&size=23"
        urls = [base + "&source=home"] + [base + f"&page={p}" for p in range(2, 6)]

        for url in urls:
            yield scrapy.Request(
                url,
                callback=self.parse_listing,
                headers={
                    "X-CSRFToken": csrf,
                    "Referer": "https://usedcars.bmw.co.uk/result/?payment_type=cash&size=23&source=home",
                },
            )

    def parse_listing(self, response):

        data = json.loads(response.text)

        for car in data["results"]:
            engine = car.get("engine", {}).get("cc")

            item_data = {
                "model": car["title"],
                "name": car["derivative"],
                "mileage": car["mileage"],
                "registered": car["registration"]["date"],
                "engine": engine if engine else None,
                "range_": car.get("consumption", {})
                .get("range", {})
                .get("values", {})
                .get("total"),
                "fuel": car["fuel"],
                "transmission": car["transmission"],
                "registration": car["identification"]["registration"],
            }

            detail_url = f"https://usedcars.bmw.co.uk/vehicle/{car['advert_id']}"

            yield scrapy.Request(
                detail_url,
                callback=self.parse_detail,
                cb_kwargs={"item_data": item_data},
            )

    def parse_detail(self, response, item_data):

        scripts = response.css("script::text").getall()
        script = next((s for s in scripts if "UVL.AD" in s), None)

        if script:
            match = re.search(r"UVL\.AD = ({.*?});", script, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                item_data["exterior"] = data.get("colour", {}).get(
                    "manufacturer_colour"
                )
                item_data["upholstery"] = data.get("specification", {}).get("interior")
        else:
            item_data["exterior"] = None
            item_data["upholstery"] = None

        item = BmwScraperItem(**item_data)
        yield item
