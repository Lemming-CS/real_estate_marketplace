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
- `GET /api/v1/favorites`
- `POST /api/v1/favorites/{listingPublicId}`
- `DELETE /api/v1/favorites/{listingPublicId}`

### Conversations and messaging
- `POST /api/v1/conversations/from-listing/{listingPublicId}`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{conversationPublicId}`
- `POST /api/v1/conversations/{conversationPublicId}/messages`
- `POST /api/v1/conversations/{conversationPublicId}/read`
- `GET /api/v1/conversations/{conversationPublicId}/attachments/{attachmentPublicId}`

### Notifications
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{notificationId}/read`
- `GET /api/v1/notifications/unread-count`

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

## Discovery Query Params
- `q`: keyword search across title and description
- `category_public_id`: exact category filter
- `city`: partial city/location match
- `min_price`: lower price bound
- `max_price`: upper price bound
- `status`: allowed on owner/admin listing contexts
- `sort`: `newest`, `oldest`, `price_asc`, `price_desc`
- `promoted_first`: optional boolean ordering hint
- `page`: 1-based page number
- `page_size`: page size, capped at 50

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
  "items": [
    {
      "public_id": "lst_123",
      "title": "MacBook Air M2 16GB 512GB",
      "price_amount": "950.00",
      "currency_code": "USD",
      "status": "published",
      "item_condition": "like_new",
      "city": "Bishkek",
      "is_promoted": true,
      "category": {
        "public_id": "cat_laptops",
        "name": "Laptops",
        "slug": "laptops"
      },
      "seller": {
        "public_id": "usr_seller",
        "username": "demo_seller",
        "full_name": "Demo Seller",
        "profile_image_path": "profile-images/usr_seller/avatar.jpg"
      },
      "primary_media": {
        "public_id": "med_1",
        "asset_key": "listings/lst_123/0e4...jpg",
        "mime_type": "image/jpeg",
        "is_primary": true
      },
      "published_at": "2026-03-26T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 132,
    "total_pages": 7
  }
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
  },
  "owner": {
    "public_id": "usr_seller",
    "username": "demo_seller",
    "full_name": "Demo Seller",
    "bio": "Laptop specialist",
    "profile_image_path": "profile-images/usr_seller/avatar.jpg",
    "active_listing_count": 12,
    "created_at": "2026-01-01T10:00:00Z"
  }
}
```

### Favorites list item
```json
{
  "items": [
    {
      "created_at": "2026-03-27T10:00:00Z",
      "listing_public_id": "lst_123",
      "is_available": false,
      "unavailable_reason": "listing_archived",
      "listing": {
        "public_id": "lst_123",
        "title": "MacBook Air M2 16GB 512GB",
        "price_amount": "950.00",
        "currency_code": "USD",
        "status": "archived",
        "item_condition": "like_new",
        "city": "Bishkek",
        "is_promoted": false,
        "category": {
          "public_id": "cat_laptops",
          "name": "Laptops",
          "slug": "laptops"
        },
        "seller": {
          "public_id": "usr_seller",
          "username": "demo_seller",
          "full_name": "Demo Seller",
          "profile_image_path": null
        },
        "primary_media": null,
        "published_at": null,
        "created_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-27T10:00:00Z"
      }
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1
  }
}
```

### Conversation detail
```json
{
  "public_id": "cnv_123",
  "status": "active",
  "listing": {
    "public_id": "lst_123",
    "title": "MacBook Air M2 16GB 512GB",
    "status": "published",
    "primary_media_asset_key": "listings/lst_123/cover.jpg"
  },
  "buyer_user_id": "usr_buyer",
  "seller_user_id": "usr_seller",
  "counterparty": {
    "public_id": "usr_seller",
    "username": "demo_seller",
    "full_name": "Demo Seller",
    "profile_image_path": null
  },
  "unread_count": 1,
  "last_message_at": "2026-03-27T10:00:00Z",
  "messages": [
    {
      "public_id": "msg_123",
      "sender_user_id": "usr_buyer",
      "body": "Is this still available?",
      "message_type": "text",
      "status": "sent",
      "read_at": null,
      "created_at": "2026-03-27T10:00:00Z",
      "attachments": [
        {
          "public_id": "att_123",
          "attachment_type": "file",
          "file_name": "invoice.pdf",
          "mime_type": "application/pdf",
          "file_size_bytes": 10240,
          "download_url": "/api/v1/conversations/cnv_123/attachments/att_123"
        }
      ]
    }
  ]
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
