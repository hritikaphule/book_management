from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os   

# Async MyMongodb database URL
MONGO_URL = "mongodb+srv://hritikaphule16:CVpNpwHiQFonkLoG@cluster0.jt6ob.mongodb.net/"
# MongoDB Setup
client = AsyncIOMotorClient(MONGO_URL)
db = client["webbackend"]  # Database name
collection = db["books"]        # Collection name



# FastAPI app
app = FastAPI()

# Pydantic Model for Input
class BookCreate(BaseModel):
    title: str
    author: str
    published_year: int
    isbn: str
    price: float

class BookOut(BookCreate):
    id: str

# Helper to convert MongoDB ObjectId to string
def book_serializer(book) -> dict:
    return {
        "id": str(book["_id"]),
        "title": book["title"],
        "author": book["author"],
        "published_year": book["published_year"],
        "isbn": book["isbn"],
        "price": book["price"],
    }

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the Book Management API using MongoDB!"}

@app.get("/books", response_model=List[BookOut])
async def get_books():
    books = await collection.find().to_list(100)  # Fetch all books
    return [book_serializer(book) for book in books]

@app.get("/books/{book_id}", response_model=BookOut)
async def get_book(book_id: str):
    book = await collection.find_one({"_id": ObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book_serializer(book)

@app.post("/books", response_model=BookOut)
async def create_book(book: BookCreate):
    new_book = book.dict()
    result = await collection.insert_one(new_book)  # Insert into MongoDB
    created_book = await collection.find_one({"_id": result.inserted_id})
    return book_serializer(created_book)

@app.put("/books/{book_id}", response_model=BookOut)
async def update_book(book_id: str, updated_book: BookCreate):
    result = await collection.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": updated_book.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    updated = await collection.find_one({"_id": ObjectId(book_id)})
    return book_serializer(updated)

@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    result = await collection.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": f"Book with ID {book_id} has been deleted"}