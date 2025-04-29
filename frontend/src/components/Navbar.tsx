import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DashboardIcon from '@mui/icons-material/Dashboard';

const Navbar: React.FC = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Sales Order Processor
        </Typography>
        <Box>
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
            startIcon={<DashboardIcon />}
          >
            Dashboard
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/upload"
            startIcon={<UploadFileIcon />}
          >
            Upload
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 
