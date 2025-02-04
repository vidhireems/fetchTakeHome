
from datetime import datetime
import math
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import uuid
import re

app = FastAPI()

# In-memory storage for receipt points
receiptPoints = {}

# Define Receipt Item schema
class Item(BaseModel):
    shortDescription: str 
    price: str 

# Define Receipt schema
class Receipt(BaseModel):
    retailer: str 
    purchaseDate: str 
    purchaseTime: str 
    items: list[Item]
    total: str 


# GET API - Retrieve points by reciept id
@app.get("/receipts/{id}/points")
def getPoints(id: str):
        if id not in receiptPoints:
            raise HTTPException(status_code=404, detail="Receipt ID not found")
        return {"points": receiptPoints[id]}


# POST API - Process new Receipt
@app.post("/receipts/process")
def processReceipt(receipt: Receipt):

    # Validate Receipt
    validateInput(receipt)

    # Generate a random UUID
    uniqueId = str(uuid.uuid4())  
    
    # Calculate points for the receipt
    calculatePoint(receipt.retailer, 
                   receipt.purchaseDate, 
                   receipt.purchaseTime,
                   receipt.items, 
                   receipt.total,
                   uniqueId )

    # Return JSON object for uuid
    return {"uuid": uniqueId}



def validateInput(receipt):

    # Validate retailer format
    if not re.match(r"^[\w\s\-&]+$", receipt.retailer):
        raise HTTPException(status_code=400, detail="Invalid retailer format.")

    # Validate the format of purchaseDate ('YYYY-MM-DD')
    try:
        datetime.strptime(receipt.purchaseDate, "%Y-%m-%d") 
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid purchaseDate format. Expected YYYY-MM-DD.")

    # Validate the format of purchaseTime ('HH:MM')
    if not re.match(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$", receipt.purchaseTime):
        raise HTTPException(status_code=400, detail="Invalid purchaseTime format. Expected HH:MM.")

    # Validate that at least one item is present
    if not receipt.items:
        raise HTTPException(status_code=400, detail="The receipt must have at least one item.")
    
    # Validate each item
    for item in receipt.items:
        if not re.match(r"^[\w\s\-]+$", item.shortDescription):
            raise HTTPException(status_code=400, detail=f"Invalid item description: {item.shortDescription}")

        if not re.match(r"^\d+\.\d{2}$", item.price):
            raise HTTPException(status_code=400, detail=f"Invalid item price: {item.price}")
    
    # Validate the format of total
    if not re.match(r"^\d+\.\d{2}$", receipt.total):
        raise HTTPException(status_code=400, detail="Invalid total amount format.")


    
# Calculate points based on the rules for the provided receipt and 
# store in the map 
def calculatePoint(retailer, purchaseDate,  purchaseTime, items, total, uniqueId):
    points = 0

    # One point for every alphanumeric character in the retailer name.
    for ch in retailer:
        if ch.isalnum():
            points += 1

    # 6 points if the day in the purchase date is odd.
    day = int(purchaseDate[-2:]) 
    if day % 2 == 1:
        points += 6

    # 10 points if the time of purchase is after 2:00pm and before 4:00pm.
    time = int(purchaseTime[:2])
    if 14 <= time < 16: 
        points += 10
    
    # 5 points for every two items on the receipt
    points += (len(items) // 2) * 5
   
    # If the trimmed length of the item description is a multiple of 3, 
    # multiply the price by 0.2 and round up to the nearest integer. 
    # The result is the number of points earned.
    for item in items:
        description = item.shortDescription.strip()
        if len(description) % 3 == 0:
            points += math.ceil(float(item.price) * 0.2)
    
    # 50 points if the total is a round dollar amount with no cents
    cents = int(total.split('.')[-1])
    if cents == 0:
        points += 50
    
    # 25 points if the total is a multiple of 0.25
    if cents % 25 == 0:
        points += 25
   
    # Store points in the map
    receiptPoints[uniqueId] = points

# Function to start server on localhost port 8000
def main():
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
