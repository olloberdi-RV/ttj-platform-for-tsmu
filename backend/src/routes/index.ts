import { Router } from 'express';
import { authRouter } from './auth.routes.js';
import { structureRouter } from './structure.routes.js';
import { studentsRouter } from './students.routes.js';
import { paymentsRouter } from './payments.routes.js';
import { auditRouter } from './audit.routes.js';
import { importRouter } from './import.routes.js';
import { dashboardRouter } from './dashboard.routes.js';

export const apiRouter = Router();

apiRouter.use('/auth', authRouter);
apiRouter.use('/', structureRouter);
apiRouter.use('/', studentsRouter);
apiRouter.use('/', paymentsRouter);
apiRouter.use('/', auditRouter);
apiRouter.use('/', importRouter);
apiRouter.use('/', dashboardRouter);
