# API Contract Overview

## API Principles
- Base path: `/api/v1`
- JSON request and response bodies except for multipart upload endpoints
- Backend is the only authority for permissions, status transitions, and payment state
- Public discovery endpoints expose only approved and active listings
- Admin endpoints use a dedicated `/api/v1/admin` prefix

## Route Groups
### Authentication
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### User and profile
- `GET /api/v1/me`
- `PATCH /api/v1/me`
- `GET /api/v1/me/addresses`
- `POST /api/v1/me/addresses`
- `PATCH /api/v1/me/addresses/{addressId}`
- `DELETE /api/v1/me/addresses/{addressId}`
- `POST /api/v1/me/seller-profile`
- `GET /api/v1/me/seller-profile`

### Catalog
- `GET /api/v1/categories`
- `GET /api/v1/categories/{categorySlug}`
- `GET /api/v1/brands`
- `GET /api/v1/categories/{categorySlug}/attributes`

### Listings
- `GET /api/v1/listings`
- `GET /api/v1/listings/{listingId}`
- `POST /api/v1/listings`
- `PATCH /api/v1/listings/{listingId}`
- `POST /api/v1/listings/{listingId}/submit`
- `POST /api/v1/listings/{listingId}/archive`
- `POST /api/v1/listings/{listingId}/mark-sold`
- `GET /api/v1/me/listings`

### Media uploads
- `POST /api/v1/uploads/images`
- `DELETE /api/v1/uploads/images/{assetId}`

### Favorites
- `GET /api/v1/me/favorites`
- `POST /api/v1/listings/{listingId}/favorite`
- `DELETE /api/v1/listings/{listingId}/favorite`

### Orders
- `POST /api/v1/orders`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{orderId}`
- `POST /api/v1/orders/{orderId}/cancel`
- `POST /api/v1/orders/{orderId}/confirm`
- `POST /api/v1/orders/{orderId}/mark-paid`
- `POST /api/v1/orders/{orderId}/mark-delivered`

### Promotions and payments
- `GET /api/v1/promotion-plans`
- `POST /api/v1/listings/{listingId}/promotions`
- `GET /api/v1/me/promotions`
- `GET /api/v1/payments`
- `GET /api/v1/payments/{paymentId}`

### Notifications
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{notificationId}/read`

### Admin
- `POST /api/v1/admin/auth/login`
- `POST /api/v1/admin/auth/refresh`
- `POST /api/v1/admin/auth/logout`
- `GET /api/v1/admin/dashboard/summary`
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/{userId}`
- `POST /api/v1/admin/users/{userId}/block`
- `POST /api/v1/admin/users/{userId}/unblock`
- `GET /api/v1/admin/listings`
- `GET /api/v1/admin/listings/{listingId}`
- `POST /api/v1/admin/listings/{listingId}/approve`
- `POST /api/v1/admin/listings/{listingId}/reject`
- `GET /api/v1/admin/orders`
- `GET /api/v1/admin/orders/{orderId}`
- `POST /api/v1/admin/orders/{orderId}/override-status`
- `GET /api/v1/admin/promotions`
- `POST /api/v1/admin/promotions/{promotionId}/cancel`
- `GET /api/v1/admin/audit-logs`

## High-Level Request / Response Shapes
### Auth token response
```json
{
  "access_token": "jwt",
  "access_token_expires_in": 900,
  "refresh_token": "opaque-token-or-cookie-backed-session",
  "refresh_token_expires_in": 2592000,
  "user": {
    "id": "usr_123",
    "email": "seller.demo@example.com",
    "full_name": "Demo Seller",
    "roles": ["buyer", "seller"],
    "status": "active",
    "locale": "en"
  }
}
```

### User profile
```json
{
  "id": "usr_123",
  "email": "buyer.demo@example.com",
  "full_name": "Demo Buyer",
  "phone": "+996700000000",
  "roles": ["buyer"],
  "status": "active",
  "locale": "en",
  "seller_profile": null
}
```

### Category and attribute metadata
```json
{
  "id": "cat_laptops",
  "name": "Laptops",
  "slug": "laptops",
  "parent_id": "cat_computers",
  "attributes": [
    {
      "code": "ram_gb",
      "label": "RAM",
      "type": "number",
      "required": true,
      "filterable": true,
      "unit": "GB"
    }
  ]
}
```

### Listing summary
```json
{
  "id": "lst_123",
  "title": "MacBook Air M2 16GB 512GB",
  "price": {
    "amount": "950.00",
    "currency": "USD"
  },
  "category": {
    "id": "cat_laptops",
    "name": "Laptops",
    "slug": "laptops"
  },
  "brand": {
    "id": "brand_apple",
    "name": "Apple"
  },
  "condition": "used_like_new",
  "city": "Bishkek",
  "primary_image_url": "https://...",
  "is_favorited": false,
  "is_promoted": true,
  "published_at": "2026-03-26T10:00:00Z"
}
```

### Listing detail
```json
{
  "id": "lst_123",
  "title": "MacBook Air M2 16GB 512GB",
  "description": "Well-kept laptop with charger and box.",
  "price": {
    "amount": "950.00",
    "currency": "USD"
  },
  "status": "published",
  "condition": "used_like_new",
  "category": {
    "id": "cat_laptops",
    "name": "Laptops",
    "slug": "laptops"
  },
  "brand": {
    "id": "brand_apple",
    "name": "Apple"
  },
  "attributes": [
    {
      "code": "ram_gb",
      "label": "RAM",
      "type": "number",
      "value": 16,
      "unit": "GB"
    }
  ],
  "images": [
    {
      "id": "img_1",
      "url": "https://...",
      "sort_order": 1,
      "is_primary": true
    }
  ],
  "seller": {
    "id": "usr_seller",
    "display_name": "Demo Seller",
    "verified": true
  },
  "promotion": {
    "status": "active",
    "plan_code": "top_7_days"
  }
}
```

### Create listing request
```json
{
  "title": "MacBook Air M2 16GB 512GB",
  "description": "Well-kept laptop with charger and box.",
  "category_id": "cat_laptops",
  "brand_id": "brand_apple",
  "condition": "used_like_new",
  "price_amount": "950.00",
  "currency_code": "USD",
  "city": "Bishkek",
  "attribute_values": [
    {
      "attribute_code": "ram_gb",
      "value": 16
    }
  ],
  "image_asset_ids": ["asset_1", "asset_2"]
}
```

### Order response
```json
{
  "id": "ord_123",
  "listing_id": "lst_123",
  "buyer_id": "usr_buyer",
  "seller_id": "usr_seller",
  "status": "pending_confirmation",
  "payment_method": "cash_on_delivery",
  "payment_status": "pending",
  "quantity": 1,
  "unit_price": {
    "amount": "950.00",
    "currency": "USD"
  },
  "total_price": {
    "amount": "950.00",
    "currency": "USD"
  },
  "shipping_address": {
    "city": "Bishkek",
    "line1": "Example street 1"
  },
  "created_at": "2026-03-26T11:00:00Z"
}
```

### Promotion response
```json
{
  "id": "promo_123",
  "listing_id": "lst_123",
  "plan": {
    "code": "top_7_days",
    "duration_days": 7,
    "price_amount": "15.00",
    "currency": "USD"
  },
  "status": "pending_payment",
  "payment_id": "pay_123",
  "start_at": null,
  "end_at": null
}
```

## Auth Flow
1. User registers or logs in.
2. Backend returns short-lived access token and refresh token/session.
3. Client sends access token in `Authorization: Bearer <token>`.
4. On expiry, client calls refresh endpoint.
5. Backend rotates refresh token and returns a new access token.
6. Logout revokes the refresh token/session.
7. Admin uses the same core auth domain with stricter role checks and admin route prefix.

## Pagination Shape
All list endpoints should return a consistent pagination envelope:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total_items": 200,
  "total_pages": 10,
  "has_next": true,
  "has_previous": false
}
```

Recommended defaults:

- default page size: `20`
- max page size: `100`
- stable sort field required on list endpoints

## Error Response Shape
Application errors should be normalized:

```json
{
  "error": {
    "code": "listing_not_found",
    "message": "Listing not found.",
    "details": {
      "listing_id": "lst_missing"
    },
    "request_id": "req_123",
    "timestamp": "2026-03-26T12:00:00Z"
  }
}
```

Error code categories:

- validation errors
- authentication errors
- authorization errors
- domain rule violations
- not found errors
- conflict errors
- internal server errors

## Admin Endpoint Notes
- Admin endpoints must never trust client-supplied role data.
- Sensitive admin mutations should accept a `reason` field where appropriate.
- Admin list endpoints should support filters by status, date range, and actor when useful.
- Audit logs should be read-only through the API.
- Admin overrides should create audit records and often a domain event or history row.
