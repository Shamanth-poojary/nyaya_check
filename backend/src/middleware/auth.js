import jwt from 'jsonwebtoken';
import { query } from '../config/db.js';

export const requireAuth = async (req, res, next) => {
  try {
    const cookieName = process.env.COOKIE_NAME || 'auth_token';
    const token = req.cookies?.[cookieName];

    if (!token) {
      return res.status(401).json({
        success: false,
        error: 'Unauthenticated. Access token is missing.'
      });
    }

    const secret = process.env.JWT_SECRET;
    if (!secret) {
      console.error('JWT_SECRET is not defined in environment variables.');
      return res.status(500).json({
        success: false,
        error: 'Internal server error.'
      });
    }

    let decoded;
    try {
      decoded = jwt.verify(token, secret);
    } catch (err) {
      return res.status(401).json({
        success: false,
        error: 'Invalid or expired session token.'
      });
    }

    const userResult = await query(
      'SELECT id, email, name, role, badge_id, zone FROM users WHERE id = $1',
      [decoded.userId]
    );

    if (userResult.rows.length === 0) {
      return res.status(401).json({
        success: false,
        error: 'User associated with session was not found.'
      });
    }

    req.user = userResult.rows[0];
    next();
  } catch (error) {
    return res.status(500).json({
      success: false,
      error: 'Internal server error.'
    });
  }
};

export const requireRole = (allowedRoles) => {
  return (req, res, next) => {
    if (!req.user || !req.user.role) {
      return res.status(401).json({
        success: false,
        error: 'Unauthenticated.'
      });
    }

    const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        error: 'Forbidden. You do not have permission to access this resource.'
      });
    }

    next();
  };
};
