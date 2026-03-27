import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { useAuth } from '@/core/auth/auth-context';
import { QueryState } from '@/shared/components/query-state';
import { TableCard } from '@/shared/components/table-card';

export function ConversationsReviewPage() {
  const auth = useAuth();
  const [scope, setScope] = useState({ listing_public_id: '', user_public_id: '' });
  const [selectedConversation, setSelectedConversation] = useState(null);

  const conversationsQuery = useQuery({
    queryKey: ['admin-conversations', scope],
    queryFn: () => auth.authenticatedRequest('/admin/conversations/review', { query: scope }),
    enabled: Boolean(scope.listing_public_id || scope.user_public_id),
  });

  const detailQuery = useQuery({
    queryKey: ['admin-conversation-detail', selectedConversation, scope],
    queryFn: () =>
      auth.authenticatedRequest(`/admin/conversations/${selectedConversation}/review`, {
        query: scope,
      }),
    enabled: Boolean(selectedConversation),
  });

  const rows = conversationsQuery.data?.items ?? [];
  const detail = detailQuery.data;

  return (
    <section className="page-section">
      <header className="page-header">
        <p className="eyebrow">Scoped Message Oversight</p>
        <h1>Review conversations only within an abuse or listing context</h1>
        <p className="page-copy">This page intentionally requires a listing or user scope before loading any conversation data.</p>
      </header>

      <div className="toolbar toolbar--wrap">
        <input className="toolbar-input" placeholder="Listing public ID" value={scope.listing_public_id} onChange={(event) => setScope((current) => ({ ...current, listing_public_id: event.target.value }))} />
        <input className="toolbar-input" placeholder="User public ID" value={scope.user_public_id} onChange={(event) => setScope((current) => ({ ...current, user_public_id: event.target.value }))} />
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
                    <td>{conversation.buyer_username} / {conversation.seller_username}</td>
                    <td>{conversation.message_count}</td>
                    <td>
                      <button className="secondary-button" type="button" onClick={() => setSelectedConversation(conversation.public_id)}>
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
                      <span>{new Date(message.created_at).toLocaleString()}</span>
                    </header>
                    <p>{message.body ?? 'Attachment only'}</p>
                    {message.attachments.length ? (
                      <ul className="attachment-list">
                        {message.attachments.map((attachment) => (
                          <li key={attachment.public_id}>{attachment.file_name} ({attachment.mime_type})</li>
                        ))}
                      </ul>
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
