import os
from google.cloud import firestore

FIRESTORE_PROJECT = "qwiklabs-gcp-02-78983e2eb373"

def seed_database():
    print(f"Connecting to Firestore project: {FIRESTORE_PROJECT}")
    db = firestore.Client(project=FIRESTORE_PROJECT, database="(default)")

    # 1. Seed recipes collection
    recipes = [
        {
            "id": "mediterranean_chickpea_salad",
            "name": "Mediterranean Chickpea Salad",
            "cuisine": "Mediterranean",
            "calories": 420,
            "prep_time_mins": 15,
            "ingredients": ["chickpeas", "cucumber", "cherry tomatoes", "red onion", "feta cheese", "olive oil", "lemon juice"],
            "instructions": "Combine washed veggies and drained chickpeas in a large bowl. Toss with olive oil and lemon juice. Top with crumbled feta.",
            "dietary_tags": ["vegetarian", "gluten-free", "high-fiber"]
        },
        {
            "id": "quinoa_veggie_stir_fry",
            "name": "Quinoa Veggie Stir Fry",
            "cuisine": "Asian",
            "calories": 380,
            "prep_time_mins": 20,
            "ingredients": ["quinoa", "broccoli", "bell pepper", "carrots", "soy sauce", "sesame oil", "garlic", "ginger"],
            "instructions": "Cook quinoa. Sauté chopped garlic, ginger, and vegetables in sesame oil. Mix in cooked quinoa and soy sauce.",
            "dietary_tags": ["vegan", "gluten-free"]
        },
        {
            "id": "grilled_lemon_herb_chicken",
            "name": "Grilled Lemon Herb Chicken",
            "cuisine": "American",
            "calories": 520,
            "prep_time_mins": 30,
            "ingredients": ["chicken breast", "lemon juice", "olive oil", "rosemary", "thyme", "garlic", "asparagus"],
            "instructions": "Marinate chicken in lemon juice, olive oil, and herbs. Grill until internal temp reaches 165°F. Serve with grilled asparagus.",
            "dietary_tags": ["high-protein", "keto", "gluten-free"]
        }
    ]

    print("Seeding 'recipes' collection...")
    for recipe in recipes:
        recipe_id = recipe["id"]
        db.collection("recipes").document(recipe_id).set(recipe)
        print(f"  ✓ Added recipe: {recipe['name']}")

    # 2. Seed pantry collection
    pantry_items = [
        {"id": "pantry_chickpeas", "item_name": "Chickpeas (canned)", "quantity": "3 cans", "category": "Canned Goods"},
        {"id": "pantry_olive_oil", "item_name": "Extra Virgin Olive Oil", "quantity": "1 bottle (500ml)", "category": "Oils & Condiments"},
        {"id": "pantry_quinoa", "item_name": "Quinoa", "quantity": "2 lbs", "category": "Grains"},
        {"id": "pantry_feta", "item_name": "Feta Cheese", "quantity": "200g", "category": "Dairy"},
        {"id": "pantry_lemons", "item_name": "Fresh Lemons", "quantity": "5 whole", "category": "Produce"}
    ]

    print("Seeding 'pantry' collection...")
    for item in pantry_items:
        item_id = item["id"]
        db.collection("pantry").document(item_id).set(item)
        print(f"  ✓ Added pantry item: {item['item_name']}")

    print("\nDatabase seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
