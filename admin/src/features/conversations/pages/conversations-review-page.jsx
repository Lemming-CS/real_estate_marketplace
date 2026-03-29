import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { TableCard } from '@/shared/components/table-card';

export function ConversationsReviewPage() {
  const auth = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [scope, setScope] = useState({
    listing_public_id: searchParams.get('listing_public_id') ?? '',
    user_public_id: searchParams.get('user_public_id') ?? '',
  });
  const [selectedConversation, setSelectedConversation] = useState(null);

  useEffect(() => {
    setScope({
      listing_public_id: searchParams.get('listing_public_id') ?? '',
      user_public_id: searchParams.get('user_public_id') ?? '',
    });
    setSelectedConversation(null);
  }, [searchParams]);

  const conversationsQuery = useQuery({
    queryKey: ['admin-conversations', scope],
    queryFn: () =>
      auth.authenticatedRequest('/admin/conversations/review', {
        query: scope,
      }),
    enabled: Boolean(scope.listing_public_id || scope.user_public_id),
  });

  const detailQuery = useQuery({
    queryKey: ['admin-conversation-detail', selectedConversation, scope],
    queryFn: () =>
      auth.authenticatedRequest(
        `/admin/conversations/${selectedConversation}/review`,
        {
          query: scope,
        },
      ),
    enabled: Boolean(selectedConversation),
  });

  const rows = conversationsQuery.data?.items ?? [];
  const detail = detailQuery.data;

  function updateScope(nextScope) {
    setScope(nextScope);
    const nextParams = new URLSearchParams();
    if (nextScope.listing_public_id) {
      nextParams.set('listing_public_id', nextScope.listing_public_id);
    }
    if (nextScope.user_public_id) {
      nextParams.set('user_public_id', nextScope.user_public_id);
    }
    setSearchParams(nextParams);
  }

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Scoped Message Oversight</p>
        <h1>Review conversations only within an abuse or listing context</h1>
        <p className="page-copy">
          This page intentionally requires a listing or user scope before
          loading any conversation data.
        </p>
      </header>

      <div className="toolbar toolbar--wrap">
        <input
          className="toolbar-input"
          placeholder="Listing public ID"
          value={scope.listing_public_id}
          onChange={(event) =>
            updateScope({ ...scope, listing_public_id: event.target.value })
          }
        />
        <input
          className="toolbar-input"
          placeholder="User public ID"
          value={scope.user_public_id}
          onChange={(event) =>
            updateScope({ ...scope, user_public_id: event.target.value })
          }
        />
      </div>

      <div className="split-grid split-grid--wide">
        <TableCard title="Scoped conversations">
          <QueryState
            isLoading={conversationsQuery.isLoading}
            error={conversationsQuery.error}
            isEmpty={!rows.length}
            emptyMessage="Provide a listing or user scope to review conversations."
          >
            <table className="data-table">
              <thead>
                <tr>
                  <th>Listing</th>
                  <th>Buyer / Seller</th>
                  <th>Messages</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {rows.map((conversation) => (
                  <tr key={conversation.public_id}>
                    <td>{conversation.listing_title ?? 'No listing'}</td>
                    <td>
                      {conversation.buyer_username} /{' '}
                      {conversation.seller_username}
                      <div className="muted-text">
                        <Link
                          className="inline-link"
                          to={`/users/${conversation.buyer_public_id}`}
                        >
                          Buyer
                        </Link>
                        {' / '}
                        <Link
                          className="inline-link"
                          to={`/users/${conversation.seller_public_id}`}
                        >
                          Seller
                        </Link>
                      </div>
                    </td>
                    <td>{conversation.message_count}</td>
                    <td>
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() =>
                          setSelectedConversation(conversation.public_id)
                        }
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </QueryState>
        </TableCard>

        <TableCard title="Conversation detail">
          <QueryState
            isLoading={detailQuery.isLoading}
            error={detailQuery.error}
            isEmpty={!detail}
            emptyMessage="Select a scoped conversation to inspect its messages."
          >
            {detail ? (
              <div className="conversation-thread">
                {detail.messages.map((message) => (
                  <article key={message.public_id} className="thread-message">
                    <header>
                      <strong>{message.sender_username}</strong>
                      <span>
                        {new Date(message.created_at).toLocaleString()}
                      </span>
                    </header>
                    <p>{message.body ?? 'Attachment only'}</p>
                    {message.attachments.length ? (
                      <div className="attachment-grid">
                        {message.attachments.map((attachment) => (
                          <ConversationAttachmentPreview
                            key={attachment.public_id}
                            attachment={attachment}
                            scope={scope}
                          />
                        ))}
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            ) : null}
          </QueryState>
        </TableCard>
      </div>
    </section>
  );
}

function ConversationAttachmentPreview({ attachment, scope }) {
  const auth = useAuth();
  const isImage = attachment.mime_type?.startsWith('image/');
  const [previewUrl, setPreviewUrl] = useState('');
  const [isLoading, setIsLoading] = useState(isImage);
  const [error, setError] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    if (!isImage) {
      return undefined;
    }

    let isActive = true;
    let objectUrl = '';

    async function loadPreview() {
      setIsLoading(true);
      setError(null);
      try {
        const blob = await auth.authenticatedBlobRequest(attachment.download_url, {
          query: scope,
        });
        if (!isActive) {
          return;
        }
        objectUrl = window.URL.createObjectURL(blob);
        setPreviewUrl(objectUrl);
      } catch (nextError) {
        if (!isActive) {
          return;
        }
        setError(nextError);
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    loadPreview();

    return () => {
      isActive = false;
      if (objectUrl) {
        window.URL.revokeObjectURL(objectUrl);
      }
    };
  }, [attachment.download_url, auth, isImage, scope]);

  async function handleDownload() {
    setIsDownloading(true);
    setError(null);
    try {
      const blob = await auth.authenticatedBlobRequest(attachment.download_url, {
        query: scope,
      });
      const objectUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = objectUrl;
      anchor.download = attachment.file_name;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000);
    } catch (nextError) {
      setError(nextError);
    } finally {
      setIsDownloading(false);
    }
  }

  if (isImage) {
    if (isLoading) {
      return <div className="attachment-preview">Loading preview...</div>;
    }
    if (!previewUrl) {
      return (
        <button
          className="attachment-file"
          type="button"
          onClick={handleDownload}
        >
          {error ? 'Preview unavailable. Download image.' : 'Open image'}
        </button>
      );
    }
    return (
      <button
        className="attachment-preview"
        type="button"
        onClick={() => window.open(previewUrl, '_blank', 'noopener,noreferrer')}
      >
        <img
          src={previewUrl}
          alt={attachment.file_name}
          className="attachment-image"
        />
      </button>
    );
  }

  return (
    <button
      className="attachment-file"
      type="button"
      onClick={handleDownload}
      disabled={isDownloading}
      title={error?.message ?? attachment.file_name}
    >
      {isDownloading ? 'Downloading...' : `📄 ${attachment.file_name}`}
    </button>
  );
}
