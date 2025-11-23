"""Corpus of grocery items for randomized test data generation.

This module contains a comprehensive list of common grocery items with realistic
pricing ranges, departments, units, and shelf life information.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GroceryItemTemplate:
    """Template for a grocery item with pricing constraints.

    Attributes:
        description: Name/description of the item.
        department: Store department where item is located.
        price_min: Minimum realistic price for the item.
        price_max: Maximum realistic price for the item.
        unit: Unit of measurement (ea, lb, gal, bag, box, btl, doz, etc.).
        shelf_life: Expected shelf life (e.g., "7d", "14d", "365d").
        cost_ratio_min: Minimum cost as ratio of price (e.g., 0.40 = 40%).
        cost_ratio_max: Maximum cost as ratio of price (e.g., 0.60 = 60%).
    """

    description: str
    department: str
    price_min: float
    price_max: float
    unit: str
    shelf_life: str
    cost_ratio_min: float = 0.40
    cost_ratio_max: float = 0.60


# =============================================================================
# PRODUCE DEPARTMENT (~45 items)
# =============================================================================
PRODUCE_ITEMS = [
    # Fruits
    GroceryItemTemplate("Honeycrisp Apples", "Produce", 2.49, 3.99, "lb", "14d"),
    GroceryItemTemplate("Gala Apples", "Produce", 1.49, 2.49, "lb", "14d"),
    GroceryItemTemplate("Granny Smith Apples", "Produce", 1.49, 2.49, "lb", "14d"),
    GroceryItemTemplate("Bananas", "Produce", 0.49, 0.79, "lb", "7d"),
    GroceryItemTemplate("Organic Bananas", "Produce", 0.69, 0.99, "lb", "7d"),
    GroceryItemTemplate("Strawberries", "Produce", 2.99, 4.99, "lb", "5d"),
    GroceryItemTemplate("Blueberries", "Produce", 3.49, 5.99, "pt", "7d"),
    GroceryItemTemplate("Raspberries", "Produce", 3.99, 5.99, "pt", "5d"),
    GroceryItemTemplate("Blackberries", "Produce", 3.49, 5.49, "pt", "5d"),
    GroceryItemTemplate("Red Grapes", "Produce", 2.49, 3.99, "lb", "7d"),
    GroceryItemTemplate("Green Grapes", "Produce", 2.49, 3.99, "lb", "7d"),
    GroceryItemTemplate("Watermelon", "Produce", 5.99, 8.99, "ea", "7d"),
    GroceryItemTemplate("Cantaloupe", "Produce", 2.99, 4.49, "ea", "7d"),
    GroceryItemTemplate("Honeydew Melon", "Produce", 3.49, 4.99, "ea", "7d"),
    GroceryItemTemplate("Oranges", "Produce", 0.79, 1.29, "ea", "14d"),
    GroceryItemTemplate("Navel Oranges", "Produce", 1.29, 1.99, "lb", "14d"),
    GroceryItemTemplate("Lemons", "Produce", 0.49, 0.79, "ea", "21d"),
    GroceryItemTemplate("Limes", "Produce", 0.33, 0.59, "ea", "21d"),
    GroceryItemTemplate("Avocado", "Produce", 0.99, 1.79, "ea", "5d"),
    GroceryItemTemplate("Mango", "Produce", 1.29, 1.99, "ea", "5d"),
    GroceryItemTemplate("Pineapple", "Produce", 2.99, 4.99, "ea", "7d"),
    GroceryItemTemplate("Peaches", "Produce", 1.99, 2.99, "lb", "5d"),
    GroceryItemTemplate("Plums", "Produce", 1.99, 2.99, "lb", "5d"),
    GroceryItemTemplate("Nectarines", "Produce", 1.99, 2.99, "lb", "5d"),
    GroceryItemTemplate("Cherries", "Produce", 4.99, 7.99, "lb", "7d"),
    GroceryItemTemplate("Kiwi", "Produce", 0.49, 0.79, "ea", "14d"),
    GroceryItemTemplate("Pomegranate", "Produce", 2.49, 3.49, "ea", "14d"),
    # Vegetables
    GroceryItemTemplate("Baby Carrots", "Produce", 1.99, 2.99, "bag", "21d"),
    GroceryItemTemplate("Carrots Whole", "Produce", 1.49, 2.49, "lb", "21d"),
    GroceryItemTemplate("Russet Potatoes", "Produce", 3.99, 5.99, "bag", "30d"),
    GroceryItemTemplate("Red Potatoes", "Produce", 3.49, 4.99, "bag", "30d"),
    GroceryItemTemplate("Yukon Gold Potatoes", "Produce", 3.99, 5.49, "bag", "30d"),
    GroceryItemTemplate("Sweet Potatoes", "Produce", 1.29, 1.99, "lb", "21d"),
    GroceryItemTemplate("Yellow Onions", "Produce", 0.99, 1.49, "lb", "30d"),
    GroceryItemTemplate("Red Onions", "Produce", 1.29, 1.79, "lb", "30d"),
    GroceryItemTemplate("Garlic", "Produce", 0.49, 0.79, "ea", "30d"),
    GroceryItemTemplate("Fresh Ginger", "Produce", 3.99, 5.99, "lb", "21d"),
    GroceryItemTemplate("Broccoli", "Produce", 1.99, 2.99, "lb", "7d"),
    GroceryItemTemplate("Broccoli Crown", "Produce", 1.49, 2.49, "ea", "7d"),
    GroceryItemTemplate("Cauliflower", "Produce", 2.49, 3.99, "ea", "7d"),
    GroceryItemTemplate("Celery", "Produce", 1.99, 2.99, "ea", "14d"),
    GroceryItemTemplate("Romaine Lettuce", "Produce", 1.99, 2.99, "ea", "7d"),
    GroceryItemTemplate("Iceberg Lettuce", "Produce", 1.49, 2.49, "ea", "7d"),
    GroceryItemTemplate("Baby Spinach", "Produce", 3.49, 4.99, "bag", "7d"),
    GroceryItemTemplate("Spring Mix", "Produce", 3.99, 5.49, "bag", "7d"),
    GroceryItemTemplate("Kale", "Produce", 2.49, 3.49, "bch", "7d"),
    GroceryItemTemplate("Green Bell Pepper", "Produce", 0.99, 1.49, "ea", "7d"),
    GroceryItemTemplate("Red Bell Pepper", "Produce", 1.49, 1.99, "ea", "7d"),
    GroceryItemTemplate("Yellow Bell Pepper", "Produce", 1.49, 1.99, "ea", "7d"),
    GroceryItemTemplate("Jalapeno Peppers", "Produce", 0.99, 1.49, "lb", "14d"),
    GroceryItemTemplate("Cucumber", "Produce", 0.79, 1.29, "ea", "7d"),
    GroceryItemTemplate("English Cucumber", "Produce", 1.49, 1.99, "ea", "7d"),
    GroceryItemTemplate("Zucchini", "Produce", 1.29, 1.79, "lb", "7d"),
    GroceryItemTemplate("Yellow Squash", "Produce", 1.29, 1.79, "lb", "7d"),
    GroceryItemTemplate("Roma Tomatoes", "Produce", 1.49, 2.29, "lb", "7d"),
    GroceryItemTemplate("Beefsteak Tomatoes", "Produce", 1.99, 2.99, "lb", "7d"),
    GroceryItemTemplate("Cherry Tomatoes", "Produce", 2.99, 4.49, "pt", "7d"),
    GroceryItemTemplate("Grape Tomatoes", "Produce", 2.99, 4.49, "pt", "7d"),
    GroceryItemTemplate("Mushrooms White", "Produce", 2.49, 3.49, "pkg", "7d"),
    GroceryItemTemplate("Mushrooms Cremini", "Produce", 2.99, 3.99, "pkg", "7d"),
    GroceryItemTemplate("Asparagus", "Produce", 2.99, 4.99, "bch", "5d"),
    GroceryItemTemplate("Green Beans", "Produce", 2.49, 3.49, "lb", "7d"),
    GroceryItemTemplate("Corn on the Cob", "Produce", 0.49, 0.79, "ea", "5d"),
    GroceryItemTemplate("Fresh Basil", "Produce", 2.49, 3.49, "ea", "7d"),
    GroceryItemTemplate("Fresh Cilantro", "Produce", 0.99, 1.49, "bch", "7d"),
    GroceryItemTemplate("Fresh Parsley", "Produce", 0.99, 1.49, "bch", "7d"),
    GroceryItemTemplate("Fresh Mint", "Produce", 1.99, 2.99, "ea", "7d"),
    GroceryItemTemplate("Green Onions", "Produce", 0.99, 1.49, "bch", "7d"),
]

# =============================================================================
# DAIRY DEPARTMENT (~30 items)
# =============================================================================
DAIRY_ITEMS = [
    # Milk
    GroceryItemTemplate("Whole Milk", "Dairy", 3.49, 4.49, "gal", "14d"),
    GroceryItemTemplate("2% Reduced Fat Milk", "Dairy", 3.49, 4.49, "gal", "14d"),
    GroceryItemTemplate("1% Low Fat Milk", "Dairy", 3.49, 4.49, "gal", "14d"),
    GroceryItemTemplate("Skim Milk", "Dairy", 3.29, 4.29, "gal", "14d"),
    GroceryItemTemplate("Organic Whole Milk", "Dairy", 5.99, 7.49, "gal", "14d"),
    GroceryItemTemplate("Chocolate Milk", "Dairy", 3.99, 4.99, "hgal", "14d"),
    GroceryItemTemplate("Half and Half", "Dairy", 3.49, 4.49, "qt", "14d"),
    GroceryItemTemplate("Heavy Whipping Cream", "Dairy", 4.49, 5.99, "pt", "14d"),
    # Alternative Milks
    GroceryItemTemplate("Almond Milk Original", "Dairy", 3.49, 4.49, "hgal", "30d"),
    GroceryItemTemplate("Almond Milk Vanilla", "Dairy", 3.49, 4.49, "hgal", "30d"),
    GroceryItemTemplate("Oat Milk Original", "Dairy", 3.99, 5.49, "hgal", "30d"),
    GroceryItemTemplate("Oat Milk Barista", "Dairy", 4.99, 6.49, "hgal", "30d"),
    GroceryItemTemplate("Soy Milk Original", "Dairy", 3.29, 4.29, "hgal", "30d"),
    GroceryItemTemplate("Coconut Milk", "Dairy", 3.49, 4.49, "hgal", "30d"),
    # Cheese
    GroceryItemTemplate("Sharp Cheddar Cheese", "Dairy", 4.99, 6.99, "lb", "45d"),
    GroceryItemTemplate("Mild Cheddar Cheese", "Dairy", 4.49, 6.49, "lb", "45d"),
    GroceryItemTemplate("Mozzarella Cheese", "Dairy", 4.49, 6.49, "lb", "45d"),
    GroceryItemTemplate("Shredded Mozzarella", "Dairy", 3.49, 4.99, "bag", "30d"),
    GroceryItemTemplate("Shredded Cheddar", "Dairy", 3.49, 4.99, "bag", "30d"),
    GroceryItemTemplate("Parmesan Cheese Wedge", "Dairy", 6.99, 9.99, "ea", "60d"),
    GroceryItemTemplate("Grated Parmesan", "Dairy", 4.49, 5.99, "ea", "90d"),
    GroceryItemTemplate("Swiss Cheese", "Dairy", 5.49, 7.49, "lb", "45d"),
    GroceryItemTemplate("Provolone Cheese", "Dairy", 5.49, 7.49, "lb", "45d"),
    GroceryItemTemplate("American Cheese Slices", "Dairy", 3.99, 5.49, "pkg", "60d"),
    GroceryItemTemplate("Cream Cheese", "Dairy", 2.99, 3.99, "pkg", "30d"),
    GroceryItemTemplate("Cottage Cheese", "Dairy", 3.49, 4.49, "tub", "14d"),
    GroceryItemTemplate("Ricotta Cheese", "Dairy", 3.99, 4.99, "tub", "14d"),
    GroceryItemTemplate("Feta Cheese Crumbles", "Dairy", 4.49, 5.99, "pkg", "30d"),
    GroceryItemTemplate("Blue Cheese Crumbles", "Dairy", 4.99, 6.49, "pkg", "30d"),
    GroceryItemTemplate("Goat Cheese", "Dairy", 4.99, 6.99, "pkg", "30d"),
    GroceryItemTemplate("Brie Cheese", "Dairy", 6.99, 9.99, "ea", "30d"),
    # Eggs
    GroceryItemTemplate("Large Eggs", "Dairy", 3.99, 5.99, "doz", "28d"),
    GroceryItemTemplate("Large Eggs 18ct", "Dairy", 5.99, 8.49, "pkg", "28d"),
    GroceryItemTemplate("Organic Large Eggs", "Dairy", 5.99, 7.99, "doz", "28d"),
    GroceryItemTemplate("Cage Free Eggs", "Dairy", 4.99, 6.99, "doz", "28d"),
    GroceryItemTemplate("Egg Whites", "Dairy", 4.49, 5.99, "ctn", "21d"),
    # Yogurt
    GroceryItemTemplate("Greek Yogurt Plain", "Dairy", 4.99, 6.49, "tub", "21d"),
    GroceryItemTemplate("Greek Yogurt Vanilla", "Dairy", 4.99, 6.49, "tub", "21d"),
    GroceryItemTemplate("Greek Yogurt Strawberry", "Dairy", 0.99, 1.49, "ea", "21d"),
    GroceryItemTemplate("Greek Yogurt Blueberry", "Dairy", 0.99, 1.49, "ea", "21d"),
    GroceryItemTemplate("Regular Yogurt Variety", "Dairy", 0.79, 1.19, "ea", "21d"),
    # Butter
    GroceryItemTemplate("Butter Unsalted", "Dairy", 4.49, 5.99, "lb", "60d"),
    GroceryItemTemplate("Butter Salted", "Dairy", 4.49, 5.99, "lb", "60d"),
    GroceryItemTemplate("Butter Sticks", "Dairy", 4.49, 5.99, "pkg", "60d"),
    GroceryItemTemplate("European Style Butter", "Dairy", 5.99, 7.99, "pkg", "60d"),
    # Other Dairy
    GroceryItemTemplate("Sour Cream", "Dairy", 2.49, 3.49, "tub", "21d"),
    GroceryItemTemplate("Whipped Cream", "Dairy", 3.99, 4.99, "can", "30d"),
]

# =============================================================================
# MEAT & SEAFOOD DEPARTMENT (~35 items)
# =============================================================================
MEAT_ITEMS = [
    # Beef
    GroceryItemTemplate("Ground Beef 80/20", "Meat", 5.99, 7.99, "lb", "3d"),
    GroceryItemTemplate("Ground Beef 90/10", "Meat", 6.99, 8.99, "lb", "3d"),
    GroceryItemTemplate("Ground Beef 93/7", "Meat", 7.49, 9.49, "lb", "3d"),
    GroceryItemTemplate("Ribeye Steak", "Meat", 12.99, 17.99, "lb", "3d"),
    GroceryItemTemplate("NY Strip Steak", "Meat", 11.99, 15.99, "lb", "3d"),
    GroceryItemTemplate("Sirloin Steak", "Meat", 8.99, 12.99, "lb", "3d"),
    GroceryItemTemplate("Filet Mignon", "Meat", 19.99, 29.99, "lb", "3d"),
    GroceryItemTemplate("Chuck Roast", "Meat", 6.99, 9.99, "lb", "3d"),
    GroceryItemTemplate("Beef Stew Meat", "Meat", 7.99, 10.99, "lb", "3d"),
    GroceryItemTemplate("Beef Short Ribs", "Meat", 8.99, 12.99, "lb", "3d"),
    # Poultry
    GroceryItemTemplate("Chicken Breast Boneless", "Meat", 4.99, 7.49, "lb", "3d"),
    GroceryItemTemplate("Chicken Breast Bone-In", "Meat", 3.49, 4.99, "lb", "3d"),
    GroceryItemTemplate("Chicken Thighs Boneless", "Meat", 4.49, 6.49, "lb", "3d"),
    GroceryItemTemplate("Chicken Thighs Bone-In", "Meat", 2.99, 4.49, "lb", "3d"),
    GroceryItemTemplate("Chicken Drumsticks", "Meat", 1.99, 2.99, "lb", "3d"),
    GroceryItemTemplate("Chicken Wings", "Meat", 3.99, 5.99, "lb", "3d"),
    GroceryItemTemplate("Whole Chicken", "Meat", 1.49, 2.49, "lb", "3d"),
    GroceryItemTemplate("Ground Turkey", "Meat", 5.49, 7.49, "lb", "3d"),
    GroceryItemTemplate("Turkey Breast", "Meat", 6.99, 9.99, "lb", "3d"),
    # Pork
    GroceryItemTemplate("Pork Chops Boneless", "Meat", 4.99, 6.99, "lb", "3d"),
    GroceryItemTemplate("Pork Chops Bone-In", "Meat", 3.99, 5.49, "lb", "3d"),
    GroceryItemTemplate("Pork Tenderloin", "Meat", 5.99, 8.49, "lb", "3d"),
    GroceryItemTemplate("Pork Shoulder", "Meat", 3.49, 4.99, "lb", "3d"),
    GroceryItemTemplate("Baby Back Ribs", "Meat", 6.99, 9.99, "lb", "3d"),
    GroceryItemTemplate("Ground Pork", "Meat", 4.99, 6.49, "lb", "3d"),
    GroceryItemTemplate("Bacon Thick Cut", "Meat", 6.99, 9.99, "lb", "14d"),
    GroceryItemTemplate("Bacon Regular", "Meat", 5.99, 7.99, "lb", "14d"),
    GroceryItemTemplate("Italian Sausage", "Meat", 4.99, 6.99, "lb", "7d"),
    GroceryItemTemplate("Breakfast Sausage", "Meat", 4.49, 5.99, "lb", "7d"),
    GroceryItemTemplate("Hot Dogs Beef", "Meat", 4.99, 6.99, "pkg", "30d"),
    # Seafood
    GroceryItemTemplate("Atlantic Salmon Fillet", "Meat", 9.99, 14.99, "lb", "2d"),
    GroceryItemTemplate("Sockeye Salmon", "Meat", 12.99, 17.99, "lb", "2d"),
    GroceryItemTemplate("Tilapia Fillet", "Meat", 6.99, 9.99, "lb", "2d"),
    GroceryItemTemplate("Cod Fillet", "Meat", 8.99, 12.99, "lb", "2d"),
    GroceryItemTemplate("Shrimp Large", "Meat", 9.99, 14.99, "lb", "2d"),
    GroceryItemTemplate("Shrimp Medium", "Meat", 7.99, 11.99, "lb", "2d"),
    GroceryItemTemplate("Sea Scallops", "Meat", 14.99, 22.99, "lb", "2d"),
    GroceryItemTemplate("Crab Meat", "Meat", 12.99, 18.99, "lb", "2d"),
    # Deli Meats
    GroceryItemTemplate("Deli Turkey Breast", "Meat", 8.99, 11.99, "lb", "7d"),
    GroceryItemTemplate("Deli Ham", "Meat", 7.99, 10.99, "lb", "7d"),
    GroceryItemTemplate("Deli Roast Beef", "Meat", 10.99, 14.99, "lb", "7d"),
    GroceryItemTemplate("Deli Salami", "Meat", 8.99, 12.99, "lb", "14d"),
    GroceryItemTemplate("Pepperoni Sliced", "Meat", 5.99, 7.99, "pkg", "30d"),
]

# =============================================================================
# BAKERY DEPARTMENT (~25 items)
# =============================================================================
BAKERY_ITEMS = [
    GroceryItemTemplate("Sourdough Bread", "Bakery", 3.99, 5.49, "ea", "5d"),
    GroceryItemTemplate("White Bread Sliced", "Bakery", 2.49, 3.49, "ea", "7d"),
    GroceryItemTemplate("Whole Wheat Bread", "Bakery", 2.99, 3.99, "ea", "7d"),
    GroceryItemTemplate("Multigrain Bread", "Bakery", 3.49, 4.49, "ea", "7d"),
    GroceryItemTemplate("French Baguette", "Bakery", 2.49, 3.49, "ea", "2d"),
    GroceryItemTemplate("Ciabatta Bread", "Bakery", 3.49, 4.49, "ea", "3d"),
    GroceryItemTemplate("Italian Bread", "Bakery", 2.99, 3.99, "ea", "3d"),
    GroceryItemTemplate("Rye Bread", "Bakery", 3.49, 4.49, "ea", "7d"),
    GroceryItemTemplate("Bagels Plain", "Bakery", 3.99, 4.99, "pkg", "5d"),
    GroceryItemTemplate("Bagels Everything", "Bakery", 3.99, 4.99, "pkg", "5d"),
    GroceryItemTemplate("English Muffins", "Bakery", 2.99, 3.99, "pkg", "7d"),
    GroceryItemTemplate("Croissants", "Bakery", 4.49, 5.99, "pkg", "3d"),
    GroceryItemTemplate("Dinner Rolls", "Bakery", 2.99, 3.99, "pkg", "5d"),
    GroceryItemTemplate("Hamburger Buns", "Bakery", 2.49, 3.49, "pkg", "7d"),
    GroceryItemTemplate("Hot Dog Buns", "Bakery", 2.49, 3.49, "pkg", "7d"),
    GroceryItemTemplate("Flour Tortillas", "Bakery", 2.99, 3.99, "pkg", "21d"),
    GroceryItemTemplate("Corn Tortillas", "Bakery", 2.49, 3.49, "pkg", "21d"),
    GroceryItemTemplate("Pita Bread", "Bakery", 2.99, 3.99, "pkg", "7d"),
    GroceryItemTemplate("Naan Bread", "Bakery", 3.99, 4.99, "pkg", "7d"),
    GroceryItemTemplate("Pie Crust", "Bakery", 3.49, 4.49, "pkg", "14d"),
    GroceryItemTemplate("Chocolate Chip Cookies", "Bakery", 3.99, 5.49, "pkg", "14d"),
    GroceryItemTemplate("Sugar Cookies", "Bakery", 3.49, 4.99, "pkg", "14d"),
    GroceryItemTemplate("Chocolate Cake Slice", "Bakery", 3.99, 5.49, "ea", "5d"),
    GroceryItemTemplate("Cheesecake Slice", "Bakery", 4.49, 5.99, "ea", "5d"),
    GroceryItemTemplate("Apple Pie", "Bakery", 7.99, 10.99, "ea", "5d"),
    GroceryItemTemplate("Blueberry Muffins", "Bakery", 3.99, 5.49, "pkg", "5d"),
    GroceryItemTemplate("Banana Nut Muffins", "Bakery", 3.99, 5.49, "pkg", "5d"),
    GroceryItemTemplate("Cinnamon Rolls", "Bakery", 4.49, 5.99, "pkg", "5d"),
    GroceryItemTemplate("Donuts Glazed", "Bakery", 4.99, 6.99, "pkg", "3d"),
]

# =============================================================================
# GROCERY / PANTRY DEPARTMENT (~65 items)
# =============================================================================
GROCERY_ITEMS = [
    # Breakfast
    GroceryItemTemplate("Cheerios Cereal", "Grocery", 4.29, 5.49, "box", "365d"),
    GroceryItemTemplate("Frosted Flakes", "Grocery", 4.29, 5.49, "box", "365d"),
    GroceryItemTemplate("Honey Nut Cheerios", "Grocery", 4.29, 5.49, "box", "365d"),
    GroceryItemTemplate("Raisin Bran", "Grocery", 3.99, 4.99, "box", "365d"),
    GroceryItemTemplate("Oatmeal Instant", "Grocery", 3.49, 4.49, "box", "365d"),
    GroceryItemTemplate("Oatmeal Old Fashioned", "Grocery", 3.99, 4.99, "can", "365d"),
    GroceryItemTemplate("Granola", "Grocery", 4.49, 5.99, "bag", "180d"),
    GroceryItemTemplate("Pancake Mix", "Grocery", 2.99, 3.99, "box", "365d"),
    GroceryItemTemplate("Maple Syrup", "Grocery", 6.99, 9.99, "btl", "365d"),
    # Pasta & Rice
    GroceryItemTemplate("Spaghetti Pasta", "Grocery", 1.49, 2.29, "box", "730d"),
    GroceryItemTemplate("Penne Pasta", "Grocery", 1.49, 2.29, "box", "730d"),
    GroceryItemTemplate("Fettuccine Pasta", "Grocery", 1.49, 2.29, "box", "730d"),
    GroceryItemTemplate("Elbow Macaroni", "Grocery", 1.29, 1.99, "box", "730d"),
    GroceryItemTemplate("Egg Noodles", "Grocery", 2.49, 3.49, "bag", "730d"),
    GroceryItemTemplate("White Rice Long Grain", "Grocery", 2.99, 4.49, "bag", "730d"),
    GroceryItemTemplate("Brown Rice", "Grocery", 3.49, 4.99, "bag", "365d"),
    GroceryItemTemplate("Jasmine Rice", "Grocery", 4.99, 6.99, "bag", "730d"),
    GroceryItemTemplate("Basmati Rice", "Grocery", 5.49, 7.49, "bag", "730d"),
    GroceryItemTemplate("Quinoa", "Grocery", 5.99, 7.99, "bag", "365d"),
    # Sauces & Condiments
    GroceryItemTemplate("Marinara Sauce", "Grocery", 2.99, 4.49, "jar", "365d"),
    GroceryItemTemplate("Alfredo Sauce", "Grocery", 3.49, 4.99, "jar", "365d"),
    GroceryItemTemplate("Tomato Sauce", "Grocery", 0.99, 1.49, "can", "730d"),
    GroceryItemTemplate("Crushed Tomatoes", "Grocery", 1.49, 2.29, "can", "730d"),
    GroceryItemTemplate("Diced Tomatoes", "Grocery", 1.29, 1.99, "can", "730d"),
    GroceryItemTemplate("Tomato Paste", "Grocery", 0.99, 1.49, "can", "730d"),
    GroceryItemTemplate("Ketchup", "Grocery", 2.99, 3.99, "btl", "365d"),
    GroceryItemTemplate("Mustard Yellow", "Grocery", 1.99, 2.99, "btl", "365d"),
    GroceryItemTemplate("Mustard Dijon", "Grocery", 2.99, 3.99, "jar", "365d"),
    GroceryItemTemplate("Mayonnaise", "Grocery", 3.99, 5.49, "jar", "180d"),
    GroceryItemTemplate("Soy Sauce", "Grocery", 2.99, 4.49, "btl", "730d"),
    GroceryItemTemplate("Hot Sauce", "Grocery", 2.49, 3.99, "btl", "730d"),
    GroceryItemTemplate("BBQ Sauce", "Grocery", 2.99, 4.49, "btl", "365d"),
    GroceryItemTemplate("Salsa Mild", "Grocery", 2.99, 4.49, "jar", "365d"),
    GroceryItemTemplate("Salsa Medium", "Grocery", 2.99, 4.49, "jar", "365d"),
    GroceryItemTemplate("Ranch Dressing", "Grocery", 3.49, 4.49, "btl", "180d"),
    GroceryItemTemplate("Italian Dressing", "Grocery", 2.99, 3.99, "btl", "180d"),
    GroceryItemTemplate("Balsamic Vinaigrette", "Grocery", 3.49, 4.49, "btl", "365d"),
    # Oils & Vinegars
    GroceryItemTemplate("Extra Virgin Olive Oil", "Grocery", 8.99, 12.99, "btl", "365d"),
    GroceryItemTemplate("Vegetable Oil", "Grocery", 3.99, 5.49, "btl", "365d"),
    GroceryItemTemplate("Canola Oil", "Grocery", 3.99, 5.49, "btl", "365d"),
    GroceryItemTemplate("Coconut Oil", "Grocery", 6.99, 9.99, "jar", "730d"),
    GroceryItemTemplate("Balsamic Vinegar", "Grocery", 4.99, 7.99, "btl", "730d"),
    GroceryItemTemplate("Apple Cider Vinegar", "Grocery", 3.49, 4.99, "btl", "730d"),
    GroceryItemTemplate("Red Wine Vinegar", "Grocery", 2.99, 4.49, "btl", "730d"),
    # Canned Goods
    GroceryItemTemplate("Black Beans", "Grocery", 0.99, 1.49, "can", "730d"),
    GroceryItemTemplate("Kidney Beans", "Grocery", 0.99, 1.49, "can", "730d"),
    GroceryItemTemplate("Pinto Beans", "Grocery", 0.99, 1.49, "can", "730d"),
    GroceryItemTemplate("Garbanzo Beans", "Grocery", 1.29, 1.79, "can", "730d"),
    GroceryItemTemplate("Green Beans Canned", "Grocery", 0.99, 1.49, "can", "730d"),
    GroceryItemTemplate("Corn Canned", "Grocery", 0.99, 1.49, "can", "730d"),
    GroceryItemTemplate("Peas Canned", "Grocery", 0.99, 1.49, "can", "730d"),
    GroceryItemTemplate("Chicken Broth", "Grocery", 2.49, 3.49, "ctn", "365d"),
    GroceryItemTemplate("Beef Broth", "Grocery", 2.49, 3.49, "ctn", "365d"),
    GroceryItemTemplate("Vegetable Broth", "Grocery", 2.49, 3.49, "ctn", "365d"),
    GroceryItemTemplate("Tuna Chunk Light", "Grocery", 1.29, 1.99, "can", "730d"),
    GroceryItemTemplate("Tuna Solid White", "Grocery", 2.49, 3.49, "can", "730d"),
    GroceryItemTemplate("Salmon Canned", "Grocery", 3.49, 4.99, "can", "730d"),
    # Snacks
    GroceryItemTemplate("Potato Chips Original", "Grocery", 3.99, 4.99, "bag", "90d"),
    GroceryItemTemplate("Potato Chips BBQ", "Grocery", 3.99, 4.99, "bag", "90d"),
    GroceryItemTemplate("Tortilla Chips", "Grocery", 3.49, 4.49, "bag", "90d"),
    GroceryItemTemplate("Pretzels", "Grocery", 2.99, 3.99, "bag", "180d"),
    GroceryItemTemplate("Popcorn Microwave", "Grocery", 3.49, 4.49, "box", "180d"),
    GroceryItemTemplate("Crackers Saltine", "Grocery", 2.49, 3.49, "box", "180d"),
    GroceryItemTemplate("Crackers Wheat", "Grocery", 2.99, 3.99, "box", "180d"),
    GroceryItemTemplate("Graham Crackers", "Grocery", 2.99, 3.99, "box", "180d"),
    GroceryItemTemplate("Peanuts Roasted", "Grocery", 4.99, 6.99, "jar", "180d"),
    GroceryItemTemplate("Almonds Raw", "Grocery", 7.99, 10.99, "bag", "180d"),
    GroceryItemTemplate("Mixed Nuts", "Grocery", 8.99, 11.99, "can", "180d"),
    GroceryItemTemplate("Trail Mix", "Grocery", 5.99, 7.99, "bag", "180d"),
    # Baking
    GroceryItemTemplate("All Purpose Flour", "Grocery", 2.99, 4.49, "bag", "365d"),
    GroceryItemTemplate("Bread Flour", "Grocery", 3.49, 4.99, "bag", "365d"),
    GroceryItemTemplate("Sugar White", "Grocery", 2.99, 3.99, "bag", "730d"),
    GroceryItemTemplate("Sugar Brown", "Grocery", 2.99, 3.99, "bag", "365d"),
    GroceryItemTemplate("Powdered Sugar", "Grocery", 2.49, 3.49, "bag", "365d"),
    GroceryItemTemplate("Baking Soda", "Grocery", 0.99, 1.49, "box", "730d"),
    GroceryItemTemplate("Baking Powder", "Grocery", 2.49, 3.49, "can", "365d"),
    GroceryItemTemplate("Vanilla Extract", "Grocery", 4.99, 7.99, "btl", "730d"),
    GroceryItemTemplate("Chocolate Chips", "Grocery", 2.99, 4.49, "bag", "365d"),
    GroceryItemTemplate("Cocoa Powder", "Grocery", 3.99, 5.99, "can", "730d"),
    GroceryItemTemplate("Honey", "Grocery", 5.99, 8.99, "btl", "730d"),
    # Peanut Butter & Jelly
    GroceryItemTemplate("Peanut Butter Creamy", "Grocery", 3.49, 4.99, "jar", "365d"),
    GroceryItemTemplate("Peanut Butter Crunchy", "Grocery", 3.49, 4.99, "jar", "365d"),
    GroceryItemTemplate("Almond Butter", "Grocery", 7.99, 10.99, "jar", "365d"),
    GroceryItemTemplate("Strawberry Jam", "Grocery", 2.99, 4.49, "jar", "365d"),
    GroceryItemTemplate("Grape Jelly", "Grocery", 2.49, 3.49, "jar", "365d"),
    # Beverages
    GroceryItemTemplate("Orange Juice", "Grocery", 3.99, 5.49, "hgal", "14d"),
    GroceryItemTemplate("Apple Juice", "Grocery", 2.99, 3.99, "btl", "30d"),
    GroceryItemTemplate("Grape Juice", "Grocery", 3.49, 4.49, "btl", "30d"),
    GroceryItemTemplate("Cranberry Juice", "Grocery", 3.49, 4.49, "btl", "30d"),
    GroceryItemTemplate("Coffee Ground", "Grocery", 7.99, 11.99, "bag", "180d"),
    GroceryItemTemplate("Coffee Whole Bean", "Grocery", 9.99, 13.99, "bag", "180d"),
    GroceryItemTemplate("Coffee Instant", "Grocery", 6.99, 9.99, "jar", "365d"),
    GroceryItemTemplate("Tea Bags Black", "Grocery", 3.49, 4.99, "box", "730d"),
    GroceryItemTemplate("Tea Bags Green", "Grocery", 3.49, 4.99, "box", "730d"),
    GroceryItemTemplate("Tea Bags Herbal", "Grocery", 3.99, 5.49, "box", "730d"),
    GroceryItemTemplate("Sparkling Water", "Grocery", 3.99, 5.99, "pkg", "365d"),
    GroceryItemTemplate("Cola Soda 12pk", "Grocery", 5.99, 7.99, "pkg", "180d"),
    GroceryItemTemplate("Lemon Lime Soda 12pk", "Grocery", 5.99, 7.99, "pkg", "180d"),
]

# =============================================================================
# FROZEN DEPARTMENT (~25 items)
# =============================================================================
FROZEN_ITEMS = [
    # Ice Cream
    GroceryItemTemplate("Vanilla Ice Cream", "Frozen", 4.99, 6.99, "tub", "180d"),
    GroceryItemTemplate("Chocolate Ice Cream", "Frozen", 4.99, 6.99, "tub", "180d"),
    GroceryItemTemplate("Strawberry Ice Cream", "Frozen", 4.99, 6.99, "tub", "180d"),
    GroceryItemTemplate("Ice Cream Bars", "Frozen", 4.49, 5.99, "box", "180d"),
    GroceryItemTemplate("Ice Cream Sandwiches", "Frozen", 4.49, 5.99, "box", "180d"),
    # Frozen Vegetables
    GroceryItemTemplate("Frozen Peas", "Frozen", 1.99, 2.99, "bag", "365d"),
    GroceryItemTemplate("Frozen Corn", "Frozen", 1.99, 2.99, "bag", "365d"),
    GroceryItemTemplate("Frozen Green Beans", "Frozen", 1.99, 2.99, "bag", "365d"),
    GroceryItemTemplate("Frozen Broccoli", "Frozen", 2.29, 3.29, "bag", "365d"),
    GroceryItemTemplate("Frozen Mixed Vegetables", "Frozen", 2.29, 3.29, "bag", "365d"),
    GroceryItemTemplate("Frozen Spinach", "Frozen", 1.99, 2.99, "bag", "365d"),
    # Frozen Fruits
    GroceryItemTemplate("Frozen Strawberries", "Frozen", 3.99, 5.49, "bag", "365d"),
    GroceryItemTemplate("Frozen Blueberries", "Frozen", 4.49, 5.99, "bag", "365d"),
    GroceryItemTemplate("Frozen Mixed Berries", "Frozen", 4.99, 6.49, "bag", "365d"),
    GroceryItemTemplate("Frozen Mango Chunks", "Frozen", 3.99, 5.49, "bag", "365d"),
    # Frozen Meals
    GroceryItemTemplate("Frozen Pizza Pepperoni", "Frozen", 5.99, 8.49, "ea", "180d"),
    GroceryItemTemplate("Frozen Pizza Cheese", "Frozen", 5.49, 7.99, "ea", "180d"),
    GroceryItemTemplate("Frozen Lasagna", "Frozen", 6.99, 9.99, "ea", "180d"),
    GroceryItemTemplate("Frozen Mac and Cheese", "Frozen", 3.49, 4.99, "ea", "180d"),
    GroceryItemTemplate("Frozen Chicken Nuggets", "Frozen", 6.99, 9.49, "bag", "180d"),
    GroceryItemTemplate("Frozen Fish Sticks", "Frozen", 5.99, 7.99, "box", "180d"),
    # Frozen Breakfast
    GroceryItemTemplate("Frozen Waffles", "Frozen", 2.99, 4.49, "box", "180d"),
    GroceryItemTemplate("Frozen Pancakes", "Frozen", 2.99, 4.49, "box", "180d"),
    GroceryItemTemplate("Frozen Breakfast Burritos", "Frozen", 3.99, 5.49, "pkg", "180d"),
    GroceryItemTemplate("Frozen Hash Browns", "Frozen", 2.99, 3.99, "bag", "365d"),
]

# =============================================================================
# PHARMACY / HEALTH DEPARTMENT (~20 items)
# =============================================================================
PHARMACY_ITEMS = [
    # Pain Relief
    GroceryItemTemplate("Ibuprofen 200mg", "Pharmacy", 7.99, 10.99, "btl", "730d"),
    GroceryItemTemplate("Acetaminophen 500mg", "Pharmacy", 6.99, 9.99, "btl", "730d"),
    GroceryItemTemplate("Aspirin 325mg", "Pharmacy", 5.99, 8.49, "btl", "730d"),
    GroceryItemTemplate("Naproxen Sodium", "Pharmacy", 8.99, 11.99, "btl", "730d"),
    # Cold & Flu
    GroceryItemTemplate("Cold and Flu Medicine", "Pharmacy", 9.99, 13.99, "box", "730d"),
    GroceryItemTemplate("Cough Syrup", "Pharmacy", 7.99, 10.99, "btl", "730d"),
    GroceryItemTemplate("Throat Lozenges", "Pharmacy", 4.99, 6.99, "bag", "730d"),
    GroceryItemTemplate("Nasal Decongestant", "Pharmacy", 6.99, 9.99, "box", "730d"),
    # Allergy
    GroceryItemTemplate("Allergy Relief 24hr", "Pharmacy", 14.99, 21.99, "box", "730d"),
    GroceryItemTemplate("Antihistamine Tablets", "Pharmacy", 8.99, 12.99, "box", "730d"),
    # Digestive
    GroceryItemTemplate("Antacid Tablets", "Pharmacy", 5.99, 8.49, "btl", "730d"),
    GroceryItemTemplate("Heartburn Relief", "Pharmacy", 9.99, 14.99, "box", "730d"),
    GroceryItemTemplate("Anti Diarrheal", "Pharmacy", 6.99, 9.99, "box", "730d"),
    GroceryItemTemplate("Fiber Supplement", "Pharmacy", 11.99, 15.99, "btl", "365d"),
    # Vitamins
    GroceryItemTemplate("Multivitamin Daily", "Pharmacy", 9.99, 14.99, "btl", "730d"),
    GroceryItemTemplate("Vitamin C 1000mg", "Pharmacy", 7.99, 11.99, "btl", "730d"),
    GroceryItemTemplate("Vitamin D3 2000IU", "Pharmacy", 8.99, 12.99, "btl", "730d"),
    GroceryItemTemplate("Fish Oil Omega-3", "Pharmacy", 12.99, 18.99, "btl", "365d"),
    GroceryItemTemplate("Calcium Plus D", "Pharmacy", 9.99, 13.99, "btl", "730d"),
    GroceryItemTemplate("Probiotic Supplement", "Pharmacy", 19.99, 29.99, "btl", "365d"),
    # First Aid
    GroceryItemTemplate("Bandages Assorted", "Pharmacy", 3.99, 5.99, "box", "730d"),
    GroceryItemTemplate("Antibiotic Ointment", "Pharmacy", 4.99, 7.49, "tube", "730d"),
    GroceryItemTemplate("Hydrogen Peroxide", "Pharmacy", 1.99, 2.99, "btl", "730d"),
    GroceryItemTemplate("Rubbing Alcohol", "Pharmacy", 2.49, 3.49, "btl", "730d"),
]

# =============================================================================
# COMPLETE CORPUS
# =============================================================================
GROCERY_CORPUS: list[GroceryItemTemplate] = (
    PRODUCE_ITEMS + DAIRY_ITEMS + MEAT_ITEMS + BAKERY_ITEMS + GROCERY_ITEMS + FROZEN_ITEMS + PHARMACY_ITEMS
)

# Total item count for reference
CORPUS_SIZE = len(GROCERY_CORPUS)
