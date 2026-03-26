import { createBrowserRouter } from 'react-router-dom';

import { AppLayout } from '@/app/layout/app-layout';
import { DashboardPage } from '@/features/dashboard/pages/dashboard-page';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
    ],
  },
]);

