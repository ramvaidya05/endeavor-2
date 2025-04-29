import React, { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  CircularProgress,
  Snackbar,
  Alert as MuiAlert,
  Card,
  CardContent,
} from '@mui/material';
import axios from 'axios';

interface LineItem {
  id: number;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  catalog_match_id?: string;
  catalog_match_data?: {
    id: string;
    name: string;
    description: string;
  };
  confidence_score: number;
}

interface EditDialogProps {
  open: boolean;
  onClose: () => void;
  item: LineItem;
  onSave: (updatedItem: LineItem) => void;
}

const EditDialog: React.FC<EditDialogProps> = ({ open, onClose, item, onSave }) => {
  const [editedItem, setEditedItem] = useState<LineItem>(item);

  const handleChange = (field: keyof LineItem, value: any) => {
    setEditedItem(prev => ({
      ...prev,
      [field]: value,
      total_price: field === 'quantity' || field === 'unit_price' 
        ? Number(value) * (field === 'quantity' ? prev.unit_price : prev.quantity)
        : prev.total_price
    }));
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Edit Line Item</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            label="Description"
            value={editedItem.description}
            onChange={(e) => handleChange('description', e.target.value)}
            fullWidth
            multiline
            rows={3}
          />
          <TextField
            label="Quantity"
            type="number"
            value={editedItem.quantity}
            onChange={(e) => handleChange('quantity', Number(e.target.value))}
          />
          <TextField
            label="Unit Price"
            type="number"
            value={editedItem.unit_price}
            onChange={(e) => handleChange('unit_price', Number(e.target.value))}
          />
          <TextField
            label="Total Price"
            type="number"
            value={editedItem.total_price}
            disabled
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={() => onSave(editedItem)} variant="contained" color="primary">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const OrderDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [order, setOrder] = useState<any>(null);
  const [editItem, setEditItem] = useState<LineItem | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/orders/${id}`);
        setLineItems(response.data.line_items);
        setOrder(response.data.order);
      } catch (err) {
        setError('Failed to fetch order details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleEditSave = async (updatedItem: LineItem) => {
    try {
      const response = await axios.put(
        `http://localhost:8000/orders/${id}/line-items/${updatedItem.id}`,
        updatedItem
      );

      if (response.status === 200) {
        setLineItems(prev =>
          prev.map(item => (item.id === updatedItem.id ? updatedItem : item))
        );
        setSuccessMessage('Item updated successfully');
      }
    } catch (error) {
      setError('Failed to update item');
      console.error('Error updating line item:', error);
    }
    setEditItem(null);
  };

  const handleExport = async () => {
    try {
      const response = await axios.get(
        `http://localhost:8000/orders/${id}/export`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `order_${id}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      setSuccessMessage('Order exported successfully');
    } catch (err) {
      setError('Failed to export order');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  const totalOrderValue = lineItems.reduce((sum, item) => sum + item.total_price, 0);

  return (
    <Box sx={{ p: 3, maxWidth: 1200, margin: '0 auto' }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5" component="h1">
              Order Details
            </Typography>
            <Button variant="contained" color="primary" onClick={handleExport}>
              Export to CSV
            </Button>
          </Box>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            Order ID: {id}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            Filename: {order?.original_filename}
          </Typography>
          <Typography variant="h6" color="primary" sx={{ mt: 2 }}>
            Total Order Value: ${totalOrderValue.toFixed(2)}
          </Typography>
        </CardContent>
      </Card>

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Description</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Unit Price</TableCell>
              <TableCell align="right">Total Price</TableCell>
              <TableCell>Catalog Match</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {lineItems.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.description}</TableCell>
                <TableCell align="right">{item.quantity}</TableCell>
                <TableCell align="right">${item.unit_price.toFixed(2)}</TableCell>
                <TableCell align="right">${item.total_price.toFixed(2)}</TableCell>
                <TableCell>
                  {item.catalog_match_data ? (
                    <Chip
                      label={item.catalog_match_data.name}
                      color="success"
                      title={item.catalog_match_data.description}
                    />
                  ) : (
                    <Chip label="No match" color="error" />
                  )}
                </TableCell>
                <TableCell align="center">
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setEditItem(item)}
                  >
                    Edit
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {editItem && (
        <EditDialog
          open={true}
          onClose={() => setEditItem(null)}
          item={editItem}
          onSave={handleEditSave}
        />
      )}

      <Snackbar
        open={!!successMessage}
        autoHideDuration={3000}
        onClose={() => setSuccessMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <MuiAlert 
          elevation={6} 
          variant="filled" 
          severity="success"
          onClose={() => setSuccessMessage(null)}
        >
          {successMessage}
        </MuiAlert>
      </Snackbar>
    </Box>
  );
};

export default OrderDetails; 