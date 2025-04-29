import tempfile
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
from typing import List, Dict
from pydantic import BaseModel
import json
from sqlalchemy.orm import Session
from datetime import datetime
import csv
from io import StringIO
from pathlib import Path

from models import Base, SalesOrder, LineItem
from database import engine, get_db

# Create database tables
Base.metadata.create_all(bind=engine)

# API endpoints
EXTRACTION_API = "https://plankton-app-qajlk.ondigitalocean.app"  # PDF extraction API
MATCHING_API = "https://endeavor-interview-api-gzwki.ondigitalocean.app"  # Matching API

# Create FastAPI app
app = FastAPI(title="Sales Order Processing API")

# Configure CORS first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory if it doesn't exist
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount the uploads directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

class LineItemBase(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total_price: float

class LineItemCreate(LineItemBase):
    catalog_match_id: str = None
    confidence_score: float = None

class SalesOrderCreate(BaseModel):
    filename: str
    original_filename: str
    line_items: List[LineItemCreate]

class MatchRequest(BaseModel):
    description: str

class BatchMatchRequest(BaseModel):
    queries: List[str]

# Column name mappings for different PDF formats
COLUMN_MAPPINGS = {
    # Common variations of column names
    "description": ["Request Item", "Item Description", "Description", "Product", "Part Description"],
    "quantity": ["Quantity", "Amount", "Qty", "Order Qty"],
    "unit_price": ["Unit Price", "Price", "Unit Cost", "Price/Unit"],
    "total_price": ["Total", "Total Price", "Extended Price", "Line Total"]
}

def find_matching_column(item, column_type):
    """Find the matching column name in the item dictionary."""
    possible_names = COLUMN_MAPPINGS.get(column_type, [])
    for name in possible_names:
        if name in item:
            return name
    return None

def transform_extracted_item(item):
    """Transform an extracted item into our standard format."""
    transformed = {}
    
    # Find and map description
    desc_key = find_matching_column(item, "description")
    if not desc_key:
        raise ValueError("Could not find description field in extracted data")
    transformed["description"] = item[desc_key]
    
    # Find and map quantity
    qty_key = find_matching_column(item, "quantity")
    if not qty_key:
        raise ValueError("Could not find quantity field in extracted data")
    try:
        transformed["quantity"] = int(item[qty_key])
    except (ValueError, TypeError):
        transformed["quantity"] = 0
    
    # Find and map unit price
    price_key = find_matching_column(item, "unit_price")
    if price_key and item[price_key] is not None:
        try:
            transformed["unit_price"] = float(item[price_key])
        except (ValueError, TypeError):
            transformed["unit_price"] = 0.0
    else:
        transformed["unit_price"] = 0.0
    
    # Find and map total price
    total_key = find_matching_column(item, "total_price")
    if total_key and item[total_key] is not None:
        try:
            transformed["total_price"] = float(item[total_key])
        except (ValueError, TypeError):
            transformed["total_price"] = transformed["quantity"] * transformed["unit_price"]
    else:
        transformed["total_price"] = transformed["quantity"] * transformed["unit_price"]
    
    return transformed

@app.post("/upload", response_model=dict)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a PDF file for processing."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = file.filename
    unique_filename = f"{timestamp}_{original_filename}"
    
    # Save the file to the uploads directory
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as pdf_file:
        content = await file.read()
        pdf_file.write(content)
    
    try:
        # Call extraction API
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as pdf_file:
                print(f"Calling extraction API with file: {original_filename}")
                response = await client.post(
                    f"{EXTRACTION_API}/extraction_api",
                    files={"file": (original_filename, pdf_file, "application/pdf")}
                )
                print(f"Extraction API response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Extraction API error: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail=f"PDF extraction failed: {response.text}")
                
                extracted_items = response.json()
                print(f"Extracted data: {extracted_items}")
                
                # Transform extracted data to match our expected format
                transformed_items = []
                for item in extracted_items:
                    try:
                        transformed_item = transform_extracted_item(item)
                        transformed_items.append(transformed_item)
                    except ValueError as e:
                        print(f"Warning: Skipping item due to error: {str(e)}")
                        print(f"Item data: {item}")
                        continue
                
                if not transformed_items:
                    raise HTTPException(status_code=400, detail="No valid items could be extracted from the PDF")
                
                # Create sales order in database with unique filename
                db_order = SalesOrder(
                    filename=unique_filename,
                    original_filename=original_filename,
                    status="pending"
                )
                db.add(db_order)
                db.commit()
                db.refresh(db_order)
                
                # Process line items
                matched_items = []
                descriptions = [item["description"] for item in transformed_items]
                print(f"Descriptions to match: {descriptions}")
                
                # Call batch match API
                print("Calling batch match API")
                batch_response = await client.post(
                    f"{MATCHING_API}/match/batch",
                    json={"queries": descriptions}  # Remove limit parameter as it's in query params
                )
                print(f"Batch match API response status: {batch_response.status_code}")
                print(f"Raw response: {batch_response.text}")
                
                if batch_response.status_code == 200:
                    batch_matches = batch_response.json()
                    print(f"Parsed batch matches: {batch_matches}")
                    
                    # Process matches from the results dictionary
                    matched_items = []
                    for item in transformed_items:
                        description = item["description"]
                        matches = batch_matches.get("results", {}).get(description, [])
                        print(f"Matches for {description}: {matches}")
                        
                        if matches and len(matches) > 0:
                            best_match = matches[0]
                            confidence = float(best_match.get("score", 0))  # Convert to float
                            catalog_match = best_match.get("match")
                            
                            # Get catalog item details
                            catalog_item = None
                            try:
                                with open(CATALOG_FILE, "r", encoding="utf-8") as file:
                                    reader = csv.DictReader(file)
                                    for row in reader:
                                        # Create a unique ID that matches what the API returns
                                        item_description = f"{row['Type']} {row['Material']} {row['Size']} {row['Length']} {row['Coating']} {row['Thread Type']}"
                                        if item_description == catalog_match:
                                            catalog_item = {
                                                "id": catalog_match,
                                                "name": item_description,
                                                "description": row["Description"]
                                            }
                                            break
                            except Exception as e:
                                print(f"Error finding catalog item: {str(e)}")
                            
                            # Create line item in database
                            db_line_item = LineItem(
                                sales_order_id=db_order.id,
                                description=item["description"],
                                quantity=item["quantity"],
                                unit_price=item["unit_price"],
                                total_price=item["total_price"],
                                catalog_match_id=catalog_match,
                                catalog_match_data={
                                    "id": catalog_match,
                                    "name": catalog_match,
                                    "description": catalog_match
                                } if catalog_match else None,
                                confidence_score=confidence,
                                status="pending"
                            )
                            db.add(db_line_item)
                            
                            matched_items.append({
                                "line_item": item,
                                "catalog_match": catalog_item,
                                "confidence": confidence
                            })
                        else:
                            # No match found - add item without match
                            db_line_item = LineItem(
                                sales_order_id=db_order.id,
                                description=item["description"],
                                quantity=item["quantity"],
                                unit_price=item["unit_price"],
                                total_price=item["total_price"],
                                catalog_match_id=None,
                                catalog_match_data=None,
                                confidence_score=0,
                                status="pending"
                            )
                            db.add(db_line_item)
                            
                            matched_items.append({
                                "line_item": item,
                                "catalog_match": None,
                                "confidence": 0
                            })
                    
                    db.commit()
                    
                    return {
                        "id": db_order.id,
                        "filename": unique_filename,
                        "original_filename": original_filename,
                        "extracted_data": transformed_items,
                        "matched_items": matched_items
                    }
                else:
                    print(f"Batch match API error: {batch_response.text}")
                    raise HTTPException(status_code=batch_response.status_code, detail=f"Batch matching failed: {batch_response.text}")
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Could not delete temporary file {file_path}: {str(e)}")

@app.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(SalesOrder).all()
    return orders

@app.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    line_items = db.query(LineItem).filter(LineItem.sales_order_id == order_id).all()
    return {
        "order": order,
        "line_items": line_items
    }

@app.post("/orders/{order_id}/match")
def update_match(
    order_id: int,
    line_item_id: int,
    catalog_item_id: str,
    db: Session = Depends(get_db)
):
    line_item = db.query(LineItem).filter(
        LineItem.id == line_item_id,
        LineItem.sales_order_id == order_id
    ).first()
    
    if not line_item:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    # Update the match
    line_item.catalog_match_id = catalog_item_id
    line_item.status = "verified"
    db.commit()
    
    return {"message": "Match updated successfully"}

@app.get("/orders/{order_id}/export")
async def export_order(order_id: int, db: Session = Depends(get_db)):
    """Export order details to CSV."""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    line_items = db.query(LineItem).filter(LineItem.sales_order_id == order_id).all()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header with simplified columns
    writer.writerow([
        "Description",
        "Quantity",
        "Unit Price",
        "Total Price",
        "Catalog Match"  # Simplified to just show the match name
    ])
    
    # Write data with simplified columns
    for item in line_items:
        writer.writerow([
            item.description,
            item.quantity,
            item.unit_price,
            item.total_price,
            item.catalog_match_data.get("name", "") if item.catalog_match_data else "No match"
        ])
    
    # Update order status
    order.status = "exported"
    db.commit()
    
    # Return CSV file
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=order_{order_id}.csv"
        }
    )

# Get the absolute path to the catalog file
CATALOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "unique_fastener_catalog.csv")

@app.get("/catalog")
async def get_catalog():
    """Get the catalog items from the CSV file."""
    try:
        if not os.path.exists(CATALOG_FILE):
            print(f"Catalog file not found at: {CATALOG_FILE}")
            raise HTTPException(
                status_code=500,
                detail=f"Catalog file not found at: {CATALOG_FILE}"
            )
            
        catalog_items = []
        with open(CATALOG_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create a unique ID from the combination of fields
                item_id = f"{row['Type']}_{row['Material']}_{row['Size']}_{row['Length']}_{row['Coating']}_{row['Thread Type']}"
                catalog_items.append({
                    "id": item_id,
                    "name": f"{row['Type']} {row['Material']} {row['Size']} {row['Length']} {row['Coating']} {row['Thread Type']}",
                    "description": row["Description"]
                })
        return catalog_items
    except Exception as e:
        print(f"Error reading catalog file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read catalog file: {str(e)}"
        )

@app.put("/orders/{order_id}/line-items/{line_item_id}")
def update_line_item(
    order_id: int,
    line_item_id: int,
    line_item: LineItemBase,
    db: Session = Depends(get_db)
):
    """Update a line item's details."""
    db_line_item = db.query(LineItem).filter(
        LineItem.id == line_item_id,
        LineItem.sales_order_id == order_id
    ).first()
    
    if not db_line_item:
        raise HTTPException(status_code=404, detail="Line item not found")
    
    # Update the line item fields
    for field, value in line_item.dict().items():
        setattr(db_line_item, field, value)
    
    db.commit()
    db.refresh(db_line_item)
    
    return db_line_item

@app.get("/files/{filename}")
async def get_file(filename: str):
    """Get a file from the uploads directory."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 