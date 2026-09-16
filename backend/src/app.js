import express from 'express';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import dotenv from 'dotenv';
import authRoutes from './routes/authRoutes.js';
import { errorHandler } from './middleware/errorHandler.js';

dotenv.config();

export const app = express();

const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3000';

app.use(
  cors({
    origin: frontendUrl,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
  })
);

app.use(express.json());
app.use(cookieParser());

// Root endpoint health/welcome message
app.get('/', (req, res) => {
  res.status(200).json({
    status: 'ok',
    message: 'Hello from backend'
  });
});

app.get('/api', (req, res) => {
  res.status(200).json({
    status: 'ok',
    message: 'Hello from backend API'
  });
});

// Mount authentication routes under both /api/auth and /api for compatibility
app.use('/api/auth', authRoutes);
app.use('/api', authRoutes);

// 404 handler for unknown routes
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found.'
  });
});

// Centralized error handler
app.use(errorHandler);
