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
- `GET /api/v1/auth/me`
- `GET /api/v1/profile/me`
- `PATCH /api/v1/profile/me`
- `POST /api/v1/profile/me/image`
- `GET /api/v1/users/me/listings`
- `GET /api/v1/public/users/{userPublicId}`

### Catalog
- `GET /api/v1/categories`
- `GET /api/v1/admin/categories`
- `POST /api/v1/admin/categories`
- `GET /api/v1/admin/categories/{categoryPublicId}`
- `PATCH /api/v1/admin/categories/{categoryPublicId}`
- `DELETE /api/v1/admin/categories/{categoryPublicId}`

### Listings
- `GET /api/v1/listings`
- `GET /api/v1/listings/me`
- `POST /api/v1/listings`
- `PATCH /api/v1/listings/{listingPublicId}`
- `GET /api/v1/listings/{listingPublicId}`
- `POST /api/v1/listings/{listingPublicId}/submit-review`
- `POST /api/v1/listings/{listingPublicId}/archive`
- `POST /api/v1/listings/{listingPublicId}/deactivate`
- `POST /api/v1/listings/{listingPublicId}/reactivate`
- `POST /api/v1/listings/{listingPublicId}/mark-sold`

### Media uploads
- `POST /api/v1/listings/{listingPublicId}/media`
- `PUT /api/v1/listings/{listingPublicId}/media/{mediaPublicId}`
- `PATCH /api/v1/listings/{listingPublicId}/media/order`
- `POST /api/v1/listings/{listingPublicId}/media/{mediaPublicId}/primary`
- `DELETE /api/v1/listings/{listingPublicId}/media/{mediaPublicId}`

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
- `GET /api/v1/admin/categories`
- `POST /api/v1/admin/categories`
- `PATCH /api/v1/admin/categories/{categoryPublicId}`
- `DELETE /api/v1/admin/categories/{categoryPublicId}`
- `GET /api/v1/admin/listings/moderation`
- `POST /api/v1/admin/listings/{listingPublicId}/review`

## High-Level Request / Response Shapes
### Auth token response
```json
{
  "access_token": "jwt",
  "access_token_expires_in": 900,
  "refresh_token": "opaque-token-or-cookie-backed-session",
  "refresh_token_expires_in": 2592000,
  "user": {
    "public_id": "usr_123",
    "email": "seller.demo@example.com",
    "full_name": "Demo Seller",
    "roles": ["user", "seller"],
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
  "public_id": "cat_laptops",
  "name": "Laptops",
  "slug": "laptops",
  "parent_public_id": "cat_computers",
  "attributes": [
    {
      "code": "ram_gb",
      "display_name": "RAM",
      "data_type": "number",
      "is_required": true,
      "is_filterable": true,
      "unit": "GB"
    }
  ]
}
```

### Listing summary
```json
{
  "public_id": "lst_123",
  "title": "MacBook Air M2 16GB 512GB",
  "price_amount": "950.00",
  "currency_code": "USD",
  "status": "published",
  "category": {
    "public_id": "cat_laptops",
    "name": "Laptops",
    "slug": "laptops"
  },
  "seller": {
    "public_id": "usr_seller",
    "username": "demo_seller",
    "full_name": "Demo Seller"
  },
  "item_condition": "like_new",
  "city": "Bishkek",
  "primary_media": {
    "public_id": "med_1",
    "asset_key": "listings/lst_123/0e4...jpg",
    "mime_type": "image/jpeg",
    "is_primary": true
  },
  "published_at": "2026-03-26T10:00:00Z"
}
```

### Listing detail
```json
{
  "public_id": "lst_123",
  "title": "MacBook Air M2 16GB 512GB",
  "description": "Well-kept laptop with charger and box.",
  "price_amount": "950.00",
  "currency_code": "USD",
  "status": "published",
  "item_condition": "like_new",
  "category": {
    "public_id": "cat_laptops",
    "name": "Laptops",
    "slug": "laptops"
  },
  "attribute_values": [
    {
      "attribute_code": "ram_gb",
      "display_name": "RAM",
      "data_type": "number",
      "numeric_value": 16,
      "unit": "GB"
    }
  ],
  "media_items": [
    {
      "public_id": "img_1",
      "asset_key": "listings/lst_123/0e4...jpg",
      "sort_order": 0,
      "is_primary": true
    }
  ],
  "seller": {
    "public_id": "usr_seller",
    "username": "demo_seller",
    "full_name": "Demo Seller"
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
