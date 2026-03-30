# Messaging Model

## Conversation Design
- Conversations are listing-linked and represent one buyer, one seller, and one listing.
- A unique constraint on `(listing_id, buyer_user_id, seller_user_id)` prevents duplicate threads for the same buyer/seller/listing pair.
- Sellers cannot start conversations with themselves.
- Only the buyer and seller can access a conversation, its messages, and its attachments.
- Admins do not get a blanket bypass for private message content.

## Message Design
- Messages allow:
  - text only
  - attachment only
  - text plus attachment
- A message must contain either non-empty text or at least one attachment.
- `read_at` and `status` track whether the receiving participant has read a message.
- Inbox unread counts are derived from unread incoming messages for the current participant.

## Attachment Design
- `message_attachments` use `public_id` for API access.
- Stored files use generated storage keys under `MEDIA_STORAGE_PATH/messages/<conversation_public_id>/...`.
- Original display names are sanitized before storage metadata is saved.
- Supported MIME types:
  - `image/jpeg`
  - `image/png`
  - `image/webp`
  - `application/pdf`
  - `application/msword`
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - `text/plain`
- Attachment downloads are participant-only and never expose arbitrary filesystem paths.

## Notifications
- New message
- Listing approved
- Listing rejected
- Payment successful
- Promotion activated
- Promotion expired
