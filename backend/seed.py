"""Seed repeat-safe Nagercoil restaurant demonstration data.

Names and selected dish names come from public Nagercoil restaurant listings.
All prices are illustrative demo prices, not official current menu prices.
"""
from datetime import time
from decimal import Decimal

from app.database import Base, SessionLocal, engine
from app.models import Address, Cart, CartItem, Category, Food, Order, OrderItem, Restaurant, Review, User, DeliveryPerson
from app.models.commerce import OrderStatus
from app.models.user import UserRole
from app.security import hash_password, verify_password

CATEGORY_NAMES = ["Biryani", "South Indian", "North Indian", "Chinese", "Parotta & Breads", "Starters", "Desserts", "Beverages"]
IMAGE_BY_CATEGORY = {
    "Biryani": "/uploads/foods/biryani.svg", "South Indian": "/uploads/foods/vegetarian.svg",
    "North Indian": "/uploads/foods/curry.svg", "Chinese": "/uploads/foods/fried-rice.svg",
    "Parotta & Breads": "/uploads/foods/parotta.svg", "Starters": "/uploads/foods/chicken.svg",
    "Desserts": "/uploads/foods/dessert.svg", "Beverages": "/uploads/foods/beverage.svg",
}


def image_for_food(name: str, category: str) -> str:
    """Choose a local illustration that matches the dish, then its category."""
    normalized = name.lower()
    choices = (
        ("pizza", "/uploads/foods/pizza.svg"),
        ("burger", "/uploads/foods/burger.svg"),
        ("noodles", "/uploads/foods/noodles.svg"),
        ("fried rice", "/uploads/foods/fried-rice.svg"),
        ("biryani", "/uploads/foods/biryani.svg"),
        ("dosa", "/uploads/foods/dosa.svg"),
        ("uthappam", "/uploads/foods/dosa.svg"),
        ("pongal", "/uploads/foods/vegetarian.svg"),
        ("idiyappam", "/uploads/foods/dosa.svg"),
        ("vada", "/uploads/foods/vegetarian.svg"),
        ("parotta", "/uploads/foods/parotta.svg"),
        ("naan", "/uploads/foods/parotta.svg"),
        ("bread", "/uploads/foods/parotta.svg"),
        ("lime", "/uploads/foods/beverage.svg"),
        ("milk", "/uploads/foods/beverage.svg"),
        ("pepsi", "/uploads/foods/beverage.svg"),
        ("coffee", "/uploads/foods/beverage.svg"),
        ("dessert", "/uploads/foods/dessert.svg"),
        ("cake", "/uploads/foods/dessert.svg"),
        ("kesari", "/uploads/foods/dessert.svg"),
        ("chicken", "/uploads/foods/chicken.svg"),
        ("beef", "/uploads/foods/curry.svg"),
        ("mutton", "/uploads/foods/curry.svg"),
        ("curry", "/uploads/foods/curry.svg"),
        ("manchurian", "/uploads/foods/vegetarian.svg"),
        ("fries", "/uploads/foods/vegetarian.svg"),
    )
    for keyword, path in choices:
        if keyword in normalized:
            return path
    return IMAGE_BY_CATEGORY[category]

# Publicly listed Nagercoil localities; blank phone means no number is stored in the demo.
RESTAURANTS = [
    ("Dindigul Thalappakatti — Since 1957", "Biryani and South Indian restaurant serving Nagercoil.", "KP Road, Collectorate Junction, Nagercoil", "+914652490186", 4.6),
    ("Zam Zam Restaurant", "Nagercoil restaurant with Indian and Chinese menu listings.", "Veppamoodu, Nagercoil", "Not listed", 4.0),
    ("Porotta Hut Nagercoil", "Kerala-style restaurant with porotta specialities.", "Veppamoodu, Nagercoil", "Not listed", 4.0),
    ("Topi Vappa", "Nagercoil restaurant listed for biryani and Chinese dishes.", "Court Road, Nagercoil", "Not listed", 4.3),
    ("Bismi Restaurant", "Indian restaurant in Punnai Nager, Nagercoil.", "Punnai Nager, Nagercoil", "Not listed", 4.0),
    ("KOMBOZZ by Thalappakatti", "Biryani and South Indian outlet serving K.P. Road, Nagercoil.", "K.P. Road, Nagercoil", "Not listed", 4.2),
    ("KFC", "KFC outlet serving Nagercoil, Tamil Nadu.", "Nagercoil, Tamil Nadu", "Not listed", 4.4),
    ("Domino's Pizza", "Domino's Pizza outlet serving Nagercoil.", "Nagercoil, Tamil Nadu", "Not listed", 4.4),
    ("Arya Bhavan", "Vegetarian restaurant with a Court Road Nagercoil listing.", "Court Road, Nagercoil", "Not listed", 4.1),
    ("China Town", "Chinese restaurant listed in Simon Nagar, Nagercoil.", "Simon Nagar, Nagercoil", "Not listed", 3.6),
]

# restaurant index, category, name, description, illustrative INR price
FOODS = [
 (0,"Biryani","Thalappakatti Special Biryani","Seeraga samba biryani with raita and salna.",290),(0,"Biryani","Thalappakatti Chicken Biryani","Chicken biryani from the listed selection.",260),(0,"Biryani","Thalappakatti Egg Biryani","Egg biryani with aromatic rice.",210),(0,"Biryani","Thalappakatti Mushroom Biryani","Mushroom biryani with traditional spices.",220),(0,"Parotta & Breads","Butter Naan","Tandoor-baked butter naan.",55),(0,"South Indian","Chicken Kothu Idiyappam","Shredded idiyappam tossed with chicken.",210),
 (1,"Starters","Kethal Chicken","Listed Zam Zam chicken preparation.",240),(1,"Starters","Kothu Kozhi","Listed Zam Zam chicken dish.",230),(1,"North Indian","Beef Curry","Curry from the listed menu.",220),(1,"Starters","Beef Sukka","Dry roasted beef preparation.",230),(1,"Biryani","Chicken Biryani","Aromatic chicken biryani.",210),(1,"Beverages","Fresh Lime Soda","Fresh lime soda.",60),
 (2,"Parotta & Breads","Nool Porotta","Hand-pulled layered porotta.",40),(2,"Parotta & Breads","Bun Porotta","Soft, fluffy porotta.",50),(2,"Parotta & Breads","Veechu Porotta Butter","Buttery veechu porotta.",95),(2,"Parotta & Breads","Keema Porotta Chicken","Porotta with chicken keema.",220),(2,"North Indian","Butter Chicken","Creamy chicken curry.",300),(2,"Starters","Chicken Roast Half","Roasted chicken speciality.",235),
 (3,"Biryani","Topi Vappa Special Chicken Biryani","House special chicken biryani.",280),(3,"Biryani","Mutton Biryani","Mutton biryani from the listed selection.",320),(3,"South Indian","Kal Dosa","Soft kal dosa served with kurma.",55),(3,"South Indian","Onion Uthappam","Thick dosa with onion topping.",110),(3,"Starters","Tandoori Chicken","Tandoor-roasted chicken.",195),(3,"Chinese","Chicken Fried Rice","Chicken stir-fried rice.",220),
 (4,"Biryani","Chicken Biriyani","Popular Bismi chicken biriyani.",220),(4,"North Indian","Mutton Curry","Popular Bismi curry dish.",240),(4,"Starters","Beef Roast","Popular Bismi roast dish.",230),(4,"Starters","Chilli Beef","Spicy beef starter.",230),(4,"Parotta & Breads","Kerala Parotta","Layered Kerala-style parotta.",30),(4,"Beverages","Lime Juice","Fresh lime drink.",50),
 (5,"Biryani","Chicken Biryani","Chicken biryani from the outlet's biryani offering.",250),(5,"Biryani","Mutton Biryani","Mutton biryani.",320),(5,"Biryani","Veg Biryani","Vegetable biryani.",190),(5,"Starters","Chicken 65","Spiced fried chicken starter.",180),(5,"South Indian","Kal Dosa","Soft skillet dosa.",55),(5,"Beverages","Badam Milk","Chilled almond milk.",80),
 (6,"Starters","Hot & Crispy Chicken","KFC fried chicken pieces.",229),(6,"Starters","Peri Peri Chicken Strips","Spiced chicken strips.",199),(6,"North Indian","Chicken Zinger Burger","Chicken burger with zinger patty.",199),(6,"North Indian","Classic Zinger Burger","Classic chicken burger.",189),(6,"Starters","French Fries","Crispy potato fries.",99),(6,"Beverages","Pepsi","Chilled soft drink.",60),
 (7,"North Indian","Margherita Pizza","Classic cheese and tomato pizza.",199),(7,"North Indian","Farmhouse Pizza","Vegetable-topped pizza.",299),(7,"North Indian","Veg Extravaganza Pizza","Loaded vegetable pizza.",349),(7,"North Indian","Chicken Dominator Pizza","Chicken-topped pizza.",399),(7,"Parotta & Breads","Garlic Breadsticks","Garlic-seasoned breadsticks.",119),(7,"Desserts","Choco Lava Cake","Warm chocolate dessert.",109),
 (8,"South Indian","Pongal","South Indian rice and lentil breakfast dish.",90),(8,"South Indian","Special Masala Dosa","Masala dosa from the Nagercoil listing.",130),(8,"South Indian","Idiyappam","Steamed rice noodle cakes.",70),(8,"South Indian","Medu Vada","Crisp lentil fritter.",35),(8,"Beverages","Filter Coffee","South Indian filter coffee.",40),(8,"Desserts","Kesari","Semolina sweet.",55),
 (9,"Chinese","Chicken Fried Rice","Chicken stir-fried rice.",210),(9,"Chinese","Chicken Noodles","Wok-tossed chicken noodles.",210),(9,"Chinese","Veg Manchurian","Vegetable dumplings in sauce.",170),(9,"Chinese","Chicken Manchurian","Chicken in Manchurian sauce.",230),(9,"Chinese","Schezwan Fried Rice","Spicy Schezwan-style fried rice.",190),(9,"Beverages","Fresh Lime Soda","Fresh lime soda.",60),
]

def clear_demo_data(db):
    for model in (CartItem, Cart, OrderItem, Order, Review, Food, Category, Restaurant, DeliveryPerson, Address, User):
        db.query(model).delete(synchronize_session=False)
    db.commit()

def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Restaurant).count() == 10 and db.query(Restaurant).filter_by(name=RESTAURANTS[0][0]).first() and db.query(Restaurant).filter_by(phone="Not listed").count() == 9 and db.query(Food).count() == 60:
            for food in db.query(Food).all():
                category = db.get(Category, food.category_id)
                food.image = image_for_food(food.name, category.name)
            # Upgrade legacy plain-text demo passwords to bcrypt hashes.
            for user in db.query(User).all():
                if user.password_hash and not user.password_hash.startswith(("$2a$", "$2b$", "$2y$")):
                    known = {
                        "admin@example.com": "admin123",
                        "john@example.com": "password123",
                        "jane@example.com": "password123",
                        "bob@example.com": "password123",
                        "alice@example.com": "password123",
                        "restaurant1@example.com": "restaurant123",
                        "restaurant2@example.com": "restaurant123",
                        "delivery1@example.com": "delivery123",
                        "delivery2@example.com": "delivery123",
                    }.get(user.email)
                    if known and verify_password(known, user.password_hash):
                        user.password_hash = hash_password(known)
            db.commit()
            print("Seed skipped: Nagercoil demo data already exists; food image paths refreshed.")
            return
        clear_demo_data(db)
        users = [
            User(full_name="Admin User", email="admin@example.com", phone="9876543210", password_hash=hash_password("admin123"), role=UserRole.ADMIN),
            User(full_name="John Doe", email="john@example.com", phone="9876543211", password_hash=hash_password("password123"), role=UserRole.CUSTOMER),
            User(full_name="Jane Smith", email="jane@example.com", phone="9876543212", password_hash=hash_password("password123"), role=UserRole.CUSTOMER),
            User(full_name="Bob Johnson", email="bob@example.com", phone="9876543213", password_hash=hash_password("password123"), role=UserRole.CUSTOMER),
            User(full_name="Alice Williams", email="alice@example.com", phone="9876543214", password_hash=hash_password("password123"), role=UserRole.CUSTOMER),
            # Restaurant owners linked to restaurants
            User(full_name="Thalappakatti Manager", email="restaurant1@example.com", phone="9876543215", password_hash=hash_password("restaurant123"), role=UserRole.RESTAURANT, restaurant_id=None),
            User(full_name="Zam Zam Manager", email="restaurant2@example.com", phone="9876543216", password_hash=hash_password("restaurant123"), role=UserRole.RESTAURANT, restaurant_id=None),
            # Delivery persons
            User(full_name="Ravi Kumar", email="delivery1@example.com", phone="9876543217", password_hash=hash_password("delivery123"), role=UserRole.DELIVERY_PERSON),
            User(full_name="Suresh Patel", email="delivery2@example.com", phone="9876543218", password_hash=hash_password("delivery123"), role=UserRole.DELIVERY_PERSON),
        ]
        db.add_all(users); db.flush()
        categories = {name: Category(name=name) for name in CATEGORY_NAMES}; db.add_all(categories.values()); db.flush()
        restaurants = [Restaurant(name=n, description=d, address=a, phone=p, image=f"/uploads/restaurants/restaurant-{index + 1}.jpg", opening_time=time(9), closing_time=time(22), rating=r, is_active=True) for index, (n, d, a, p, r) in enumerate(RESTAURANTS)]
        db.add_all(restaurants); db.flush()
        
        # Link restaurant users to restaurants
        users[5].restaurant_id = restaurants[0].id  # Thalappakatti
        users[6].restaurant_id = restaurants[1].id  # Zam Zam
        db.commit()
        
        # Create delivery person profiles
        delivery_persons = [
            DeliveryPerson(user_id=users[7].id, phone="9876543217", vehicle_type="Bike", vehicle_number="TN74-AB1234", is_available=True),
            DeliveryPerson(user_id=users[8].id, phone="9876543218", vehicle_type="Scooter", vehicle_number="TN74-CD5678", is_available=True),
        ]
        db.add_all(delivery_persons); db.flush()
        
        foods = [Food(restaurant_id=restaurants[i].id, category_id=categories[c].id, name=n, description=d, price=Decimal(str(p)), image=image_for_food(n, c), is_available=True) for i, c, n, d, p in FOODS]
        db.add_all(foods); db.flush()
        first = Order(user_id=users[1].id, restaurant_id=restaurants[0].id, status=OrderStatus.DELIVERED, total_price=Decimal("730"), delivery_address="12 College Road, Nagercoil")
        first.items = [OrderItem(food_id=foods[1].id, name=foods[1].name, price=foods[1].price, quantity=2), OrderItem(food_id=foods[5].id, name=foods[5].name, price=foods[5].price, quantity=1)]
        second = Order(user_id=users[2].id, restaurant_id=restaurants[2].id, status=OrderStatus.PENDING, total_price=Decimal("180"), delivery_address="45 K.P. Road, Nagercoil")
        second.items = [OrderItem(food_id=foods[12].id, name=foods[12].name, price=foods[12].price, quantity=2), OrderItem(food_id=foods[13].id, name=foods[13].name, price=foods[13].price, quantity=2)]
        db.add_all([first, second])
        db.add_all([
            Review(user_id=users[1].id, restaurant_id=restaurants[0].id, rating=5, comment="The biryani was flavorful and the portion was good."),
            Review(user_id=users[2].id, food_id=foods[5].id, rating=5, comment="Chicken kothu idiyappam was really tasty."),
            Review(user_id=users[3].id, restaurant_id=restaurants[8].id, rating=4, comment="Good South Indian breakfast options."),
            Review(user_id=users[4].id, food_id=foods[12].id, rating=4, comment="Fresh food and reasonable demo pricing."),
            Review(user_id=users[1].id, restaurant_id=restaurants[2].id, rating=4, comment="Nice place for a family meal."),
        ])
        db.commit()
        print(f"Successfully seeded: {len(users)} users, {len(restaurants)} restaurants, {len(categories)} categories, {len(foods)} foods, {len(delivery_persons)} delivery persons, 2 orders, 5 reviews.")
    except Exception:
        db.rollback(); raise
    finally:
        db.close()

if __name__ == "__main__":
    run()
