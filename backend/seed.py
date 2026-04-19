"""One-time seeding of the default 'Desi Road' restaurant on startup."""
from core import db, logger
from models import MenuItem, RestaurantConfig

DEFAULT_MENU = [
    MenuItem(name="Butter Chicken Cones", price=16.99, category="main"),
    MenuItem(name="Shahi Lamb Chops", price=29.99, category="main"),
    MenuItem(name="Dal Makhani", price=15.99, category="main"),
    MenuItem(name="Palak Paneer", price=14.99, category="main"),
    MenuItem(name="Raj Kachori", price=12.99, category="starter"),
    MenuItem(name="Paneer Hardshell Tacos", price=13.99, category="main"),
    MenuItem(name="Chicken Tikka", price=16.99, category="main"),
    MenuItem(name="Chicken Biryani", price=18.99, category="main"),
    MenuItem(name="Seekh Kebab", price=15.99, category="main"),
    MenuItem(name="Garlic Naan", price=3.99, category="bread"),
    MenuItem(name="Butter Naan", price=3.49, category="bread"),
    MenuItem(name="Mango Lassi", price=5.99, category="drink"),
    MenuItem(name="Masala Chai", price=3.99, category="drink"),
    MenuItem(name="Gulab Jamun", price=6.99, category="dessert"),
    MenuItem(name="Kulfi Falooda", price=7.99, category="dessert"),
]


async def seed_default_restaurant() -> None:
    existing = await db.restaurants.find_one({"id": "default"}, {"_id": 0})
    if not existing:
        config = RestaurantConfig(id="default", menu=DEFAULT_MENU)
        await db.restaurants.insert_one(config.model_dump())
        logger.info("Seeded default Desi Road restaurant config")
