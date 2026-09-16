import bcrypt from 'bcryptjs';
import { query } from './db.js';

export const seedAdminUser = async () => {
  try {
    const adminName = process.env.ADMIN_NAME || 'Admin User';
    const adminEmail = (process.env.ADMIN_EMAIL || 'admin@example.com').trim().toLowerCase();
    const adminPassword = process.env.ADMIN_PASSWORD || 'admin123';

    // Check if admin user already exists
    const existing = await query('SELECT id, role FROM users WHERE email = $1', [adminEmail]);
    if (existing.rows.length === 0) {
      const salt = await bcrypt.genSalt(10);
      const passwordHash = await bcrypt.hash(adminPassword, salt);
      await query(
        `INSERT INTO users (name, email, password_hash, role)
         VALUES ($1, $2, $3, 'admin')`,
        [adminName, adminEmail, passwordHash]
      );
      console.log(`[Seed] Admin user created automatically from ENV: ${adminEmail}`);
    } else {
      console.log(`[Seed] Admin user already exists: ${adminEmail}`);
    }
  } catch (error) {
    console.error('[Seed Error] Failed to seed admin user:', error.message);
  }
};
