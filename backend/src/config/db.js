import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Pool } = pg;

const connectionString = process.env.DATABASE_URL;

if (!connectionString && process.env.NODE_ENV !== 'test') {
  console.warn('DATABASE_URL is not set in environment variables.');
}

const isProduction = process.env.NODE_ENV === 'production';
const requiresSSL = connectionString?.includes('sslmode=require') || isProduction;

export const pool = new Pool({
  connectionString,
  ssl: requiresSSL ? { rejectUnauthorized: false } : false
});

export const query = (text, params) => pool.query(text, params);
