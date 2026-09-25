import cors from 'cors';
import dotenv from 'dotenv';
import express from 'express';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { apiRouter } from './routes/index.js';
import { errorHandler } from './middleware/error-handler.js';

dotenv.config();

const app = express();
app.use(helmet());
const allowedOrigins = (process.env.CORS_ORIGINS ?? 'http://localhost:5173')
  .split(',')
  .map((origin) => origin.trim())
  .filter(Boolean);

app.use(
  cors({
    origin(origin, callback) {
      if (!origin || allowedOrigins.includes(origin)) {
        callback(null, true);
        return;
      }
      callback(new Error('CORS ruxsati yo‘q'));
    },
    credentials: true,
  }),
);
app.use(express.json({ limit: '1mb' }));
app.use(morgan('tiny'));
app.use(
  '/api/',
  rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 600,
    standardHeaders: true,
    legacyHeaders: false,
  }),
);

app.get('/health', (_req, res) => res.json({ ok: true }));
app.use('/api', apiRouter);
app.use(errorHandler);

export default app;
