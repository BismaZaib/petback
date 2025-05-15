from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, ValidationError
from typing import Optional, List, Union
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import shutil
from fastapi.middleware.cors import CORSMiddleware

# MongoDB configuration
MONGO_DETAILS = "mongodb+srv://bismaawan003:0000@cluster0.rm3gu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "Petiverse"

# Connect to MongoDB
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client[DATABASE_NAME]





# Helper for ObjectId handling in Pydantic models
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not v:
            raise ValueError("ObjectId empty")
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId {v}")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Base Models

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, example="john_doe")
    email: EmailStr = Field(..., example="john@example.com")
    full_name: Optional[str] = Field(None, example="John Doe")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, example="secretpassword")

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=30, example="john_updated")
    email: Optional[EmailStr] = Field(None, example="john_new@example.com")
    full_name: Optional[str] = Field(None, example="John New")
    password: Optional[str] = Field(None, min_length=6, example="newsecret")

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        orm_mode = True

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, example="Toys")
    description: Optional[str] = Field(None, example="Category for pet toys")

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50, example="Toys Updated")
    description: Optional[str] = Field(None, example="Updated description")

class CategoryInDB(CategoryBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        orm_mode = True

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Dog Toy")
    description: Optional[str] = Field(None, example="A fun dog toy")
    price: float = Field(..., gt=0, example=10.99)
    category_id: PyObjectId = Field(..., example="60b8d295f2a30c1df8fb7e98")
    image_url: Optional[str] = Field(None, example="/images/dogtoy.png")
    stock: int = Field(0, ge=0, example=25)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, example="Dog Toy Updated")
    description: Optional[str] = Field(None, example="Updated product description")
    price: Optional[float] = Field(None, gt=0, example=12.99)
    category_id: Optional[PyObjectId] = Field(None, example="60b8d295f2a30c1df8fb7e98")
    image_url: Optional[str] = Field(None, example="/images/updated.png")
    stock: Optional[int] = Field(None, ge=0, example=20)

class ProductInDB(ProductBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        orm_mode = True

class PetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, example="Buddy")
    species: str = Field(..., min_length=1, max_length=50, example="Dog")
    age: Optional[int] = Field(None, ge=0, example=3)
    owner_id: PyObjectId = Field(..., example="60b8d295f2a30c1df8fb7e9a")

class PetCreate(PetBase):
    pass

class PetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    species: Optional[str] = Field(None, min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=0)
    owner_id: Optional[PyObjectId]

class PetInDB(PetBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        orm_mode = True

class ReviewBase(BaseModel):
    product_id: PyObjectId = Field(..., example="60b8d295f2a30c1df8fb7e98")
    user_id: PyObjectId = Field(..., example="60b8d295f2a30c1df8fb7e9a")
    rating: int = Field(..., ge=1, le=5, example=5)
    comment: Optional[str] = Field(None, example="Great product!")

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

class ReviewInDB(ReviewBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        orm_mode = True

class CartItem(BaseModel):
    product_id: PyObjectId = Field(..., example="60b8d295f2a30c1df8fb7e98")
    quantity: int = Field(..., ge=1, example=2)

class CartBase(BaseModel):
    user_id: PyObjectId = Field(..., example="60b8d295f2a30c1df8fb7e9a")
    items: List[CartItem] = Field(default_factory=list)

class CartCreate(CartBase):
    pass

class CartUpdate(BaseModel):
    items: Optional[List[CartItem]]

class CartInDB(CartBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        orm_mode = True

class OrderBase(BaseModel):
    user_id: PyObjectId = Field(..., example="60b8d295f2a30c1df8fb7e9a")
    items: List[CartItem] = Field(default_factory=list)
    total_price: float = Field(..., ge=0, example=99.99)
    status: str = Field(default="pending", max_length=20, example="pending")

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=20, example="shipped")

class OrderInDB(OrderBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        orm_mode = True

# FastAPI app

app = FastAPI(title="FastAPI Marketplace with MongoDB - Fully Validated")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    allow_credentials=True,
)

# Collections

user_col = database.get_collection("users")
category_col = database.get_collection("categories")
product_col = database.get_collection("products")
pet_col = database.get_collection("pets")
review_col = database.get_collection("reviews")
cart_col = database.get_collection("carts")
order_col = database.get_collection("orders")

# Util to convert Mongo document to Pydantic model with str id
def fetch_one_or_404(collection, id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(422, detail="Invalid ObjectId")
    return collection.find_one({"_id": ObjectId(id)})

# ------------------------- User Routes -------------------------

@app.post("/users", response_model=UserInDB, status_code=201)
async def create_user(user: UserCreate = Body(...)):
    # Check unique email
    existing = await user_col.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_dict = user.dict()
    # Password should be hashed here in real app, omitted
    result = await user_col.insert_one(user_dict)
    created = await user_col.find_one({"_id": result.inserted_id})
    return UserInDB(**created)

@app.get("/users", response_model=List[UserInDB])
async def list_users():
    users = []
    cursor = user_col.find()
    async for u in cursor:
        users.append(UserInDB(**u))
    return users

@app.get("/users/{user_id}", response_model=UserInDB)
async def get_user(user_id: str):
    user = await fetch_one_or_404(user_col, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return UserInDB(**user)

@app.put("/users/{user_id}", response_model=UserInDB)
async def update_user(user_id: str, user_update: UserUpdate = Body(...)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(422, "Invalid User ID")
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        # Password hashing omitted
        pass
    result = await user_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    updated = await user_col.find_one({"_id": ObjectId(user_id)})
    return UserInDB(**updated)

@app.delete("/users/{user_id}", response_model=dict)
async def delete_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(422, "Invalid User ID")
    result = await user_col.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "User not found")
    return {"message": "User deleted"}

# ------------------------- Category Routes -------------------------

@app.post("/categories", response_model=CategoryInDB, status_code=201)
async def create_category(category: CategoryCreate = Body(...)):
    result = await category_col.insert_one(category.dict())
    created = await category_col.find_one({"_id": result.inserted_id})
    return CategoryInDB(**created)

@app.get("/categories", response_model=List[CategoryInDB])
async def list_categories():
    categories = []
    cursor = category_col.find()
    async for c in cursor:
        categories.append(CategoryInDB(**c))
    return categories

@app.get("/categories/{category_id}", response_model=CategoryInDB)
async def get_category(category_id: str):
    category = await fetch_one_or_404(category_col, category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    return CategoryInDB(**category)

@app.put("/categories/{category_id}", response_model=CategoryInDB)
async def update_category(category_id: str, category_update: CategoryUpdate = Body(...)):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(422, "Invalid Category ID")
    update_data = category_update.dict(exclude_unset=True)
    result = await category_col.update_one({"_id": ObjectId(category_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "Category not found")
    updated = await category_col.find_one({"_id": ObjectId(category_id)})
    return CategoryInDB(**updated)

@app.delete("/categories/{category_id}", response_model=dict)
async def delete_category(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(422, "Invalid Category ID")
    result = await category_col.delete_one({"_id": ObjectId(category_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Category not found")
    return {"message": "Category deleted"}

# ------------------------- Product Routes -------------------------

@app.post("/products", response_model=ProductInDB, status_code=201)
async def create_product(product: ProductCreate = Body(...)):
    # Validate category ID
    if not ObjectId.is_valid(str(product.category_id)):
        raise HTTPException(422, "Invalid Category ID")
    category = await category_col.find_one({"_id": ObjectId(product.category_id)})
    if not category:
        raise HTTPException(404, "Category not found")
    result = await product_col.insert_one(product.dict())
    created = await product_col.find_one({"_id": result.inserted_id})
    return ProductInDB(**created)

@app.get("/products", response_model=List[ProductInDB])
async def list_products():
    products = []
    cursor = product_col.find()
    async for p in cursor:
        products.append(ProductInDB(**p))
    return products

@app.get("/products/{product_id}", response_model=ProductInDB)
async def get_product(product_id: str):
    product = await fetch_one_or_404(product_col, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return ProductInDB(**product)

@app.put("/products/{product_id}", response_model=ProductInDB)
async def update_product(product_id: str, product_update: ProductUpdate = Body(...)):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(422, "Invalid Product ID")
    update_data = product_update.dict(exclude_unset=True)
    if "category_id" in update_data:
        if not ObjectId.is_valid(str(update_data["category_id"])):
            raise HTTPException(422, "Invalid Category ID")
        category = await category_col.find_one({"_id": ObjectId(update_data["category_id"])})
        if not category:
            raise HTTPException(404, "Category not found")
    result = await product_col.update_one({"_id": ObjectId(product_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "Product not found")
    updated = await product_col.find_one({"_id": ObjectId(product_id)})
    return ProductInDB(**updated)

@app.delete("/products/{product_id}", response_model=dict)
async def delete_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(422, "Invalid Product ID")
    result = await product_col.delete_one({"_id": ObjectId(product_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Product not found")
    return {"message": "Product deleted"}

# ------------------------- Pet Routes -------------------------

@app.post("/pets", response_model=PetInDB, status_code=201)
async def create_pet(pet: PetCreate = Body(...)):
    if not ObjectId.is_valid(str(pet.owner_id)):
        raise HTTPException(422, "Invalid Owner ID")
    owner = await user_col.find_one({"_id": ObjectId(pet.owner_id)})
    if not owner:
        raise HTTPException(404, "Owner not found")
    result = await pet_col.insert_one(pet.dict())
    created = await pet_col.find_one({"_id": result.inserted_id})
    return PetInDB(**created)

@app.get("/pets", response_model=List[PetInDB])
async def list_pets():
    pets = []
    cursor = pet_col.find()
    async for pet in cursor:
        pets.append(PetInDB(**pet))
    return pets

@app.get("/pets/{pet_id}", response_model=PetInDB)
async def get_pet(pet_id: str):
    pet = await fetch_one_or_404(pet_col, pet_id)
    if not pet:
        raise HTTPException(404, "Pet not found")
    return PetInDB(**pet)

@app.put("/pets/{pet_id}", response_model=PetInDB)
async def update_pet(pet_id: str, pet_update: PetUpdate = Body(...)):
    if not ObjectId.is_valid(pet_id):
        raise HTTPException(422, "Invalid Pet ID")
    update_data = pet_update.dict(exclude_unset=True)
    if "owner_id" in update_data:
        if not ObjectId.is_valid(str(update_data["owner_id"])):
            raise HTTPException(422, "Invalid Owner ID")
        owner = await user_col.find_one({"_id": ObjectId(update_data["owner_id"])})
        if not owner:
            raise HTTPException(404, "Owner not found")
    result = await pet_col.update_one({"_id": ObjectId(pet_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "Pet not found")
    updated = await pet_col.find_one({"_id": ObjectId(pet_id)})
    return PetInDB(**updated)

@app.delete("/pets/{pet_id}", response_model=dict)
async def delete_pet(pet_id: str):
    if not ObjectId.is_valid(pet_id):
        raise HTTPException(422, "Invalid Pet ID")
    result = await pet_col.delete_one({"_id": ObjectId(pet_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Pet not found")
    return {"message": "Pet deleted"}

# ------------------------- Review Routes -------------------------

@app.post("/reviews", response_model=ReviewInDB, status_code=201)
async def create_review(review: ReviewCreate = Body(...)):
    if not ObjectId.is_valid(str(review.product_id)) or not ObjectId.is_valid(str(review.user_id)):
        raise HTTPException(422, "Invalid Product ID or User ID")
    product = await product_col.find_one({"_id": ObjectId(review.product_id)})
    if not product:
        raise HTTPException(404, "Product not found")
    user = await user_col.find_one({"_id": ObjectId(review.user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    result = await review_col.insert_one(review.dict())
    created = await review_col.find_one({"_id": result.inserted_id})
    return ReviewInDB(**created)

@app.get("/reviews", response_model=List[ReviewInDB])
async def list_reviews():
    reviews = []
    cursor = review_col.find()
    async for rev in cursor:
        reviews.append(ReviewInDB(**rev))
    return reviews

@app.get("/reviews/{review_id}", response_model=ReviewInDB)
async def get_review(review_id: str):
    review = await fetch_one_or_404(review_col, review_id)
    if not review:
        raise HTTPException(404, "Review not found")
    return ReviewInDB(**review)

@app.put("/reviews/{review_id}", response_model=ReviewInDB)
async def update_review(review_id: str, review_update: ReviewUpdate = Body(...)):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(422, "Invalid Review ID")
    update_data = review_update.dict(exclude_unset=True)
    result = await review_col.update_one({"_id": ObjectId(review_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "Review not found")
    updated = await review_col.find_one({"_id": ObjectId(review_id)})
    return ReviewInDB(**updated)

@app.delete("/reviews/{review_id}", response_model=dict)
async def delete_review(review_id: str):
    if not ObjectId.is_valid(review_id):
        raise HTTPException(422, "Invalid Review ID")
    result = await review_col.delete_one({"_id": ObjectId(review_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Review not found")
    return {"message": "Review deleted"}

# ------------------------- Cart Routes -------------------------

@app.post("/carts", response_model=CartInDB, status_code=201)
async def create_cart(cart: CartCreate = Body(...)):
    if not ObjectId.is_valid(str(cart.user_id)):
        raise HTTPException(422, "Invalid User ID")
    user = await user_col.find_one({"_id": ObjectId(cart.user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    # Optionally check products exist
    for item in cart.items:
        if not ObjectId.is_valid(str(item.product_id)):
            raise HTTPException(422, "Invalid Product ID in cart")
        product = await product_col.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(404, f"Product {item.product_id} not found")
    result = await cart_col.insert_one(cart.dict())
    created = await cart_col.find_one({"_id": result.inserted_id})
    return CartInDB(**created)

@app.get("/carts", response_model=List[CartInDB])
async def list_carts():
    carts = []
    cursor = cart_col.find()
    async for c in cursor:
        carts.append(CartInDB(**c))
    return carts

@app.get("/carts/{cart_id}", response_model=CartInDB)
async def get_cart(cart_id: str):
    cart = await fetch_one_or_404(cart_col, cart_id)
    if not cart:
        raise HTTPException(404, "Cart not found")
    return CartInDB(**cart)

@app.put("/carts/{cart_id}", response_model=CartInDB)
async def update_cart(cart_id: str, cart_update: CartUpdate = Body(...)):
    if not ObjectId.is_valid(cart_id):
        raise HTTPException(422, "Invalid Cart ID")
    update_data = cart_update.dict(exclude_unset=True)
    if "items" in update_data:
        for item in update_data["items"]:
            if not ObjectId.is_valid(str(item.product_id)):
                raise HTTPException(422, "Invalid Product ID in cart")
            product = await product_col.find_one({"_id": ObjectId(item.product_id)})
            if not product:
                raise HTTPException(404, f"Product {item.product_id} not found")
    result = await cart_col.update_one({"_id": ObjectId(cart_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "Cart not found")
    updated = await cart_col.find_one({"_id": ObjectId(cart_id)})
    return CartInDB(**updated)

@app.delete("/carts/{cart_id}", response_model=dict)
async def delete_cart(cart_id: str):
    if not ObjectId.is_valid(cart_id):
        raise HTTPException(422, "Invalid Cart ID")
    result = await cart_col.delete_one({"_id": ObjectId(cart_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Cart not found")
    return {"message": "Cart deleted"}

# ------------------------- Order Routes -------------------------

@app.post("/orders", response_model=OrderInDB, status_code=201)
async def create_order(order: OrderCreate = Body(...)):
    if not ObjectId.is_valid(str(order.user_id)):
        raise HTTPException(422, "Invalid User ID")
    user = await user_col.find_one({"_id": ObjectId(order.user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    for item in order.items:
        if not ObjectId.is_valid(str(item.product_id)):
            raise HTTPException(422, "Invalid Product ID in order")
        product = await product_col.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(404, f"Product {item.product_id} not found")
    result = await order_col.insert_one(order.dict())
    created = await order_col.find_one({"_id": result.inserted_id})
    return OrderInDB(**created)

@app.get("/orders", response_model=List[OrderInDB])
async def list_orders():
    orders = []
    cursor = order_col.find()
    async for o in cursor:
        orders.append(OrderInDB(**o))
    return orders

@app.get("/orders/{order_id}", response_model=OrderInDB)
async def get_order(order_id: str):
    order = await fetch_one_or_404(order_col, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return OrderInDB(**order)

@app.put("/orders/{order_id}", response_model=OrderInDB)
async def update_order(order_id: str, order_update: OrderUpdate = Body(...)):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(422, "Invalid Order ID")
    update_data = order_update.dict(exclude_unset=True)
    result = await order_col.update_one({"_id": ObjectId(order_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(404, "Order not found")
    updated = await order_col.find_one({"_id": ObjectId(order_id)})
    return OrderInDB(**updated)

@app.delete("/orders/{order_id}", response_model=dict)
async def delete_order(order_id: str):
    if not ObjectId.is_valid(order_id):
        raise HTTPException(422, "Invalid Order ID")
    result = await order_col.delete_one({"_id": ObjectId(order_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Order not found")
    return {"message": "Order deleted"}

# ------------------------- Image Upload Route -------------------------

UPLOAD_DIR = "./uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-image", status_code=201)
async def upload_image(file: UploadFile = File(...)):
    filename = file.filename
    ext = filename.split(".")[-1].lower()
    if ext not in {"png", "jpg", "jpeg", "gif"}:
        raise HTTPException(400, "Invalid image type")
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {e}")

    return {"filename": filename, "url": f"/images/{filename}"}

from fastapi.staticfiles import StaticFiles
app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

# Root Endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Marketplace. Visit /docs for API documentation."}

