import { Router } from 'express';
import {
  register,
  login,
  logout,
  getCurrentUser,
  forgotPassword,
  changePassword
} from '../controllers/authController.js';
import { requireAuth } from '../middleware/auth.js';

const router = Router();

router.post('/register', register);
router.post('/login', login);
router.post('/logout', logout);
router.get('/me', requireAuth, getCurrentUser);

router.post('/forgot-password', forgotPassword);
router.post('/reset-password', forgotPassword); // Alias for convenience
router.post('/change-password', requireAuth, changePassword);
router.put('/change-password', requireAuth, changePassword);

export default router;
