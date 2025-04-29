# Sales Order Processing System

A full-stack application that processes sales orders and automatically matches items to a product catalog. The system extracts line items from uploaded orders and provides an interface for reviewing and managing them.

## Quick Setup

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Unix/MacOS

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The application will be running at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Implemented Features

### Order Management
1. **Order Upload and Processing**
   - Upload PDF purchase orders
   - Automatic extraction of line items
   - Storage of processed orders in database

2. **Order Details View**
   - View all line items in a clean table format
   - Edit quantities, prices, and descriptions
   - Real-time total order value calculation
   - Export orders to CSV

3. **Line Item Management**
   - Edit individual line items
   - Auto-calculation of total price based on quantity and unit price
   - Validation of numeric inputs
   - Persistent storage of changes

### Catalog Matching
1. **Automatic Matching**
   - Integration with matching API
   - Visual indicators for matched/unmatched items
   - Display of match confidence scores

2. **Match Management**
   - View catalog match details
   - Status indicators (green for matched, red for unmatched)
   - Hover tooltips with detailed match information

### User Interface Enhancements
1. **Modern Material-UI Design**
   - Clean, responsive layout
   - Card-based order summary
   - Intuitive table interface
   - Loading states and error handling

2. **Data Management**
   - Server-side persistence
   - Real-time updates
   - Error handling with user feedback
   - Success notifications

3. **Table Features**
   - Right-aligned numeric columns
   - Formatted currency values
   - Responsive column sizing
   - Action buttons for each row

## API Endpoints

### Orders
```
GET    /orders              # List all orders
GET    /orders/{id}         # Get order details
POST   /upload              # Upload new order
GET    /orders/{id}/export  # Export to CSV
```

### Line Items
```
PUT    /orders/{id}/line-items/{item_id}  # Update line item
POST   /orders/{id}/match                 # Update catalog match
```

## Development Notes

### Database
- Uses SQLAlchemy with SQLite
- Automatic table creation on startup
- Stores order metadata and line items

### Error Handling
- Frontend validation for numeric inputs
- Backend validation for data integrity
- Proper error messages and status codes
- User-friendly error displays

### Future Improvements
1. Batch processing of multiple orders
2. Advanced search and filtering
3. User authentication and roles
4. Order status tracking
5. Advanced matching algorithms
6. Customizable export formats

## Troubleshooting

### Common Issues
1. **Backend won't start**
   - Check Python version (3.8+ required)
   - Verify all dependencies are installed
   - Ensure port 8000 is available

2. **Frontend won't start**
   - Check Node.js version (14+ required)
   - Clear npm cache and node_modules
   - Verify backend URL configuration

3. **Upload issues**
   - Verify file is PDF format
   - Check file size limits
   - Ensure uploads directory exists and is writable

For any other issues, check the console logs or contact the development team. #
