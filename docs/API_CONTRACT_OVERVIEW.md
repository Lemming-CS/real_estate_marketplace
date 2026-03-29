# API Contract Overview

## Principles
- Base path: `/api/v1`
- JSON APIs except multipart upload endpoints
- backend is the authority for permissions, moderation transitions, payment state, and auditability
- public listing APIs expose only visible published listings
- admin routes live under `/api/v1/admin`

## Route Groups

### Health
- `GET /api/v1/health`

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/change-password`
- `GET /api/v1/auth/me`

### Profile And Users
- `GET /api/v1/profile/me`
- `PATCH /api/v1/profile/me`
- `POST /api/v1/profile/me/image`
- `GET /api/v1/users/me/listings`
- `GET /api/v1/public/users/{userPublicId}`
- `GET /api/v1/public/users/{userPublicId}/listings`

### Categories
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
- `DELETE /api/v1/listings/{listingPublicId}`
- `GET /api/v1/listings/{listingPublicId}`
- `POST /api/v1/listings/{listingPublicId}/publish`
- `POST /api/v1/listings/{listingPublicId}/submit-review`
- `POST /api/v1/listings/{listingPublicId}/archive`
- `POST /api/v1/listings/{listingPublicId}/deactivate`
- `POST /api/v1/listings/{listingPublicId}/reactivate`
- `POST /api/v1/listings/{listingPublicId}/mark-sold`

### Listing Media
- `POST /api/v1/listings/{listingPublicId}/media`
- `PUT /api/v1/listings/{listingPublicId}/media/{mediaPublicId}`
- `PATCH /api/v1/listings/{listingPublicId}/media/order`
- `POST /api/v1/listings/{listingPublicId}/media/{mediaPublicId}/primary`
- `DELETE /api/v1/listings/{listingPublicId}/media/{mediaPublicId}`
- `GET /api/v1/media/{assetKey:path}`

### Favorites
- `GET /api/v1/favorites`
- `POST /api/v1/favorites/{listingPublicId}`
- `DELETE /api/v1/favorites/{listingPublicId}`

### Conversations And Messaging
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

### Reports
- `POST /api/v1/reports`
- `GET /api/v1/reports/me`

### Promotions And Payments
- `GET /api/v1/promotion-packages`
- `POST /api/v1/payments/promotions/initiate`
- `GET /api/v1/payments`
- `POST /api/v1/payments/{paymentPublicId}/simulate`
- `GET /api/v1/promotions/me`

### Admin Auth
- `POST /api/v1/admin/auth/login`

### Admin Operations
- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/{userPublicId}`
- `POST /api/v1/admin/users/{userPublicId}/suspend`
- `POST /api/v1/admin/users/{userPublicId}/unsuspend`
- `GET /api/v1/admin/listings/moderation`
- `POST /api/v1/admin/listings/{listingPublicId}/review`
- `GET /api/v1/admin/reports`
- `POST /api/v1/admin/reports/{reportPublicId}/resolve`
- `GET /api/v1/admin/payments`
- `GET /api/v1/admin/promotions`
- `GET /api/v1/admin/promotion-packages`
- `POST /api/v1/admin/promotion-packages`
- `PATCH /api/v1/admin/promotion-packages/{packagePublicId}`
- `DELETE /api/v1/admin/promotion-packages/{packagePublicId}`
- `POST /api/v1/admin/promotion-packages/{packagePublicId}/activate`
- `GET /api/v1/admin/audit-logs`
- `GET /api/v1/admin/conversations`
- `GET /api/v1/admin/conversations/{conversationPublicId}`
- `GET /api/v1/admin/conversations/{conversationPublicId}/attachments/{attachmentPublicId}`

## Discovery Query Parameters
- `q`: title/description keyword
- `category_public_id`
- `purpose`: `rent` or `sale`
- `property_type`: `apartment` or `house`
- `city`
- `district`
- `min_price`
- `max_price`
- `min_area_sqm`
- `max_area_sqm`
- `room_count`
- `status`: owner/admin contexts only
- `sort`: `newest`, `oldest`, `price_asc`, `price_desc`
- `promoted_first`
- `reported_only`: admin listing review only
- `page`
- `page_size`

Price filtering and sorting use normalized KGS on the backend, while the API response remains backward compatible with original `price_amount` and `currency_code`.

## Auth Flow
1. User registers or logs in.
2. Backend returns short-lived JWT access token and longer-lived refresh token.
3. Client sends `Authorization: Bearer <token>` for authenticated requests.
4. Refresh token rotates on refresh.
5. Password-reset flow is token-based and mock-email friendly for local/demo use.

## Pagination Shape
Paginated endpoints return:

```json
{
  "items": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 42,
    "total_pages": 3
  }
}
```

## Error Shape
Standard business errors use:

```json
{
  "error": {
    "code": "listing_not_promotable",
    "message": "Only valid published listings can be promoted.",
    "details": {}
  }
}
```

Request validation errors from FastAPI use:

```json
{
  "detail": [
    {
      "loc": ["query", "min_price"],
      "msg": "min_price must be less than or equal to max_price",
      "type": "value_error"
    }
  ]
}
```

## Listing Summary Shape
```json
{
  "public_id": "lst_123",
  "title": "2-room apartment near Ala-Too Square",
  "purpose": "rent",
  "property_type": "apartment",
  "price_amount": "850.00",
  "currency_code": "USD",
  "favorites_count": 3,
  "view_count": 19,
  "status": "published",
  "city": "Bishkek",
  "district": "Lenin District",
  "map_label": "Ala-Too Square area",
  "latitude": "42.8746210",
  "longitude": "74.5697620",
  "room_count": 2,
  "area_sqm": "68.00",
  "is_promoted": true,
  "seller": {
    "public_id": "usr_seller",
    "username": "rent_host",
    "full_name": "Rent Host Demo"
  },
  "primary_media": {
    "public_id": "med_1",
    "asset_key": "listings/lst_123/cover.jpg",
    "mime_type": "image/jpeg",
    "is_primary": true
  }
}
```

## Listing Detail Shape
```json
{
  "public_id": "lst_123",
  "title": "2-room apartment near Ala-Too Square",
  "description": "Bright furnished apartment with renovated kitchen and fast internet.",
  "purpose": "rent",
  "property_type": "apartment",
  "price_amount": "850.00",
  "currency_code": "USD",
  "favorites_count": 3,
  "view_count": 19,
  "status": "published",
  "city": "Bishkek",
  "district": "Lenin District",
  "address_text": "Ala-Too Square area",
  "map_label": "Ala-Too Square area",
  "latitude": "42.8746210",
  "longitude": "74.5697620",
  "room_count": 2,
  "area_sqm": "68.00",
  "floor": 7,
  "total_floors": 12,
  "furnished": true,
  "media": [],
  "owner": {
    "public_id": "usr_seller",
    "username": "rent_host",
    "full_name": "Rent Host Demo",
    "active_listing_count": 5
  },
  "promotion_state": {
    "public_id": "prm_123",
    "status": "active",
    "target_city": "Bishkek",
    "target_category_name": "Квартиры"
  }
}
```

## Conversation Shape
```json
{
  "public_id": "cnv_123",
  "listing": {
    "public_id": "lst_123",
    "title": "2-room apartment near Ala-Too Square"
  },
  "counterparty": {
    "public_id": "usr_buyer",
    "username": "renter_demo",
    "full_name": "Renter Demo"
  },
  "messages": [
    {
      "public_id": "msg_1",
      "body": "Is this still available?",
      "attachments": []
    }
  ],
  "unread_count": 1,
  "last_message_preview": "Is this still available?"
}
```

## Promotion / Payment Initiation Shape
```json
{
  "payment": {
    "public_id": "pay_123",
    "status": "pending",
    "amount": "20.00",
    "currency_code": "USD"
  },
  "promotion": {
    "public_id": "prm_123",
    "status": "pending_payment",
    "listing_public_id": "lst_123"
  },
  "price_breakdown": {
    "unit_amount": "10.00",
    "duration_days": 14,
    "total_amount": "20.00"
  }
}
```

## Moderation Notes
- Direct publication is the normal seller path.
- `pending_review` exists only for exceptional/manual moderation use.
- Reports are the primary moderation queue.
- Admin suspension and unsuspension notes are durable and visible in admin user detail and audit logs.
