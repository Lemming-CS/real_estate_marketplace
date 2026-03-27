import { Navigate, Outlet, createBrowserRouter } from 'react-router-dom';

import { AppLayout } from '@/app/layout/app-layout';
import { useAuth } from '@/core/auth/auth-context';
import { AuditLogsPage } from '@/features/audit/pages/audit-logs-page';
import { LoginPage } from '@/features/auth/pages/login-page';
import { CategoriesPage } from '@/features/categories/pages/categories-page';
import { ConversationsReviewPage } from '@/features/conversations/pages/conversations-review-page';
import { DashboardPage } from '@/features/dashboard/pages/dashboard-page';
import { ListingsModerationPage } from '@/features/listings/pages/listings-moderation-page';
import { PaymentsPage } from '@/features/payments/pages/payments-page';
import { PromotionPackagesPage } from '@/features/promotion-packages/pages/promotion-packages-page';
import { PromotionsPage } from '@/features/promotions/pages/promotions-page';
import { ReportsPage } from '@/features/reports/pages/reports-page';
import { UserDetailPage } from '@/features/users/pages/user-detail-page';
import { UsersPage } from '@/features/users/pages/users-page';

function ProtectedRoute() {
  const auth = useAuth();

  if (auth.isBootstrapping) {
    return <div className="screen-state">Restoring admin session…</div>;
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

function LoginRoute() {
  const auth = useAuth();

  if (auth.isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <LoginPage />;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginRoute />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: '/',
        element: <AppLayout />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'users', element: <UsersPage /> },
          { path: 'users/:userPublicId', element: <UserDetailPage /> },
          { path: 'listings', element: <ListingsModerationPage /> },
          { path: 'reports', element: <ReportsPage /> },
          { path: 'payments', element: <PaymentsPage /> },
          { path: 'promotions', element: <PromotionsPage /> },
          { path: 'promotion-packages', element: <PromotionPackagesPage /> },
          { path: 'categories', element: <CategoriesPage /> },
          { path: 'audit-logs', element: <AuditLogsPage /> },
          { path: 'conversations', element: <ConversationsReviewPage /> },
        ],
      },
    ],
  },
]);
