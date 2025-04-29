import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Paper, Typography, CircularProgress, Alert } from '@mui/material';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Theme } from '@mui/material/styles';

const UploadBox = styled(Paper)(({ theme }: { theme: Theme }) => ({
  padding: theme.spacing(4),
  textAlign: 'center',
  cursor: 'pointer',
  border: `2px dashed ${theme.palette.primary.main}`,
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  },
}));

const Upload: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
      setError('Please upload a PDF file');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Navigate to the order details page with the processed data
      navigate(`/orders/${response.data.id}`);
    } catch (err) {
      setError('Failed to process the file. Please try again.');
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  }, [navigate]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: false,
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Sales Order
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Drag and drop a PDF file here, or click to select a file
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <UploadBox {...getRootProps()}>
        <input {...getInputProps()} />
        {isUploading ? (
          <CircularProgress />
        ) : (
          <>
            <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6">
              {isDragActive
                ? 'Drop the PDF here'
                : 'Drag and drop a PDF file here, or click to select'}
            </Typography>
          </>
        )}
      </UploadBox>
    </Box>
  );
};

export default Upload; 