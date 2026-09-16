export const errorHandler = (err, req, res, next) => {
  const status = err.statusCode || err.status || 500;
  
  if (status === 500) {
    console.error('Server error:', err.message);
  }

  const response = {
    success: false,
    error: status === 500 ? 'Internal server error.' : (err.message || 'An error occurred.')
  };

  if (err.errors && Array.isArray(err.errors)) {
    response.errors = err.errors;
  }

  res.status(status).json(response);
};
