import 'dart:io';

import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/messaging/data/messaging_repository.dart';
import 'package:electronics_marketplace_mobile/features/messaging/domain/messaging_models.dart';
import 'package:electronics_marketplace_mobile/features/messaging/presentation/controllers/messaging_providers.dart';
import 'package:electronics_marketplace_mobile/features/notifications/presentation/controllers/notification_providers.dart';
import 'package:electronics_marketplace_mobile/features/reports/data/reports_repository.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/network_media_image.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

class ConversationDetailScreen extends ConsumerStatefulWidget {
  const ConversationDetailScreen({
    super.key,
    required this.conversationId,
  });

  final String conversationId;

  @override
  ConsumerState<ConversationDetailScreen> createState() =>
      _ConversationDetailScreenState();
}

class _ConversationDetailScreenState
    extends ConsumerState<ConversationDetailScreen> {
  final TextEditingController _messageController = TextEditingController();
  final FocusNode _messageFocusNode = FocusNode();
  final ImagePicker _picker = ImagePicker();
  final List<File> _pendingAttachments = [];

  bool _isSending = false;
  bool _didMarkRead = false;
  bool _isOpeningAttachment = false;

  @override
  void dispose() {
    _messageController.dispose();
    _messageFocusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final conversationAsync =
        ref.watch(conversationDetailProvider(widget.conversationId));
    final authState = ref.watch(authControllerProvider);
    final currentUserId = authState.session?.user.publicId;

    return Scaffold(
      appBar: AppBar(
        title: conversationAsync.maybeWhen(
          data: (detail) => Text(detail.counterparty.fullName),
          orElse: () => Text(context.tr('Conversation', 'Диалог')),
        ),
        actions: [
          IconButton(
            onPressed: _isSending ? null : () => _reportConversation(authState),
            icon: const Icon(Icons.flag_outlined),
            tooltip:
                context.tr('Report conversation', 'Пожаловаться на диалог'),
          ),
          IconButton(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
        ],
      ),
      body: conversationAsync.when(
        data: (conversation) {
          _markReadOnce(authState);
          return Column(
            children: [
              if (conversation.listing != null)
                Material(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  child: ListTile(
                    leading: conversation.listing!.primaryMediaAssetKey == null
                        ? const Icon(Icons.home_work_outlined)
                        : ClipRRect(
                            borderRadius: BorderRadius.circular(12),
                            child: NetworkMediaImage(
                              assetKey:
                                  conversation.listing!.primaryMediaAssetKey!,
                              width: 48,
                              height: 48,
                            ),
                          ),
                    title: Text(conversation.listing!.title),
                    subtitle: Text(conversation.listing!.status),
                    onTap: () => context
                        .push('/listing/${conversation.listing!.publicId}'),
                  ),
                ),
              Expanded(
                child: conversation.messages.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Text(
                            context.tr(
                              'No messages yet. Start the conversation below.',
                              'Пока нет сообщений. Начните диалог ниже.',
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      )
                    : ListView.builder(
                        reverse: true,
                        padding: const EdgeInsets.all(16),
                        itemCount: conversation.messages.length,
                        itemBuilder: (context, index) {
                          final message = conversation.messages[
                              conversation.messages.length - 1 - index];
                          return _MessageBubble(
                            message: message,
                            isMine: message.senderUserId == currentUserId,
                            accessToken: authState.session?.accessToken,
                            onImageTap: (attachment) =>
                                _openImageViewer(authState, attachment),
                            onDocumentTap: (attachment) =>
                                _openDocumentAttachment(authState, attachment),
                          );
                        },
                      ),
              ),
              _ConversationComposer(
                controller: _messageController,
                focusNode: _messageFocusNode,
                isSending: _isSending,
                pendingAttachments: _pendingAttachments,
                onRemoveAttachment: (file) {
                  if (_isSending || !mounted) {
                    return;
                  }
                  setState(() => _pendingAttachments.remove(file));
                },
                onPickImage: _pickImage,
                onPickDocument: _pickDocument,
                onSend: _sendMessage,
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(error.toString(), textAlign: TextAlign.center),
          ),
        ),
      ),
    );
  }

  Future<void> _sendMessage() async {
    final accessToken = ref.read(authControllerProvider).session?.accessToken;
    if (accessToken == null) {
      return;
    }
    final body = _messageController.text.trim();
    if (body.isEmpty && _pendingAttachments.isEmpty) {
      _showSnackBar(
        context.tr(
          'Add a message or attachment first.',
          'Сначала добавьте сообщение или вложение.',
        ),
      );
      return;
    }

    setState(() => _isSending = true);
    try {
      await ref.read(messagingRepositoryProvider).sendMessage(
            accessToken: accessToken,
            conversationId: widget.conversationId,
            body: body,
            attachments: List<File>.from(_pendingAttachments),
          );
      if (!mounted) {
        return;
      }
      _messageController.clear();
      setState(() => _pendingAttachments.clear());
      _messageFocusNode.requestFocus();
      ref.invalidate(conversationDetailProvider(widget.conversationId));
      ref.invalidate(inboxProvider);
      ref.invalidate(conversationUnreadBadgeProvider);
      ref.invalidate(notificationUnreadCountProvider);
    } catch (error) {
      if (!mounted) {
        return;
      }
      _showSnackBar(error.toString());
    } finally {
      if (mounted) {
        setState(() => _isSending = false);
      }
    }
  }

  Future<void> _pickImage() async {
    final picked =
        await _picker.pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (!mounted || picked == null) {
      return;
    }
    setState(() => _pendingAttachments.add(File(picked.path)));
  }

  Future<void> _pickDocument() async {
    try {
      final file = await openFile(
        acceptedTypeGroups: [
          const XTypeGroup(
            label: 'documents',
            extensions: ['pdf', 'doc', 'docx', 'txt'],
          ),
        ],
      );
      if (!mounted || file == null || kIsWeb) {
        return;
      }
      final path = file.path;
      if (path.isEmpty) {
        return;
      }
      setState(() => _pendingAttachments.add(File(path)));
    } catch (_) {
      if (!mounted) {
        return;
      }
      _showSnackBar(
        context.tr(
          'Document picker is not available on this device yet.',
          'Выбор документов пока недоступен на этом устройстве.',
        ),
      );
    }
  }

  Future<void> _openImageViewer(
    AuthState authState,
    MessageAttachment attachment,
  ) async {
    final accessToken = authState.session?.accessToken;
    if (accessToken == null || !mounted) {
      return;
    }
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => _AttachmentImageViewer(
          title: attachment.fileName,
          requestPath: attachment.downloadUrl,
          accessToken: accessToken,
        ),
      ),
    );
  }

  Future<void> _openDocumentAttachment(
    AuthState authState,
    MessageAttachment attachment,
  ) async {
    final accessToken = authState.session?.accessToken;
    if (accessToken == null || _isOpeningAttachment) {
      return;
    }
    setState(() => _isOpeningAttachment = true);
    try {
      final tempDir = await getTemporaryDirectory();
      final file =
          await ref.read(messagingRepositoryProvider).downloadAttachment(
                accessToken: accessToken,
                downloadUrl: attachment.downloadUrl,
                fileName: attachment.fileName,
                directory: tempDir,
              );
      final result = await OpenFilex.open(file.path);
      if (!mounted) {
        return;
      }
      if (result.type != ResultType.done) {
        _showSnackBar(
          context.tr(
            'Document downloaded but could not be opened on this device.',
            'Документ загружен, но не удалось открыть его на этом устройстве.',
          ),
        );
      }
    } catch (error) {
      if (!mounted) {
        return;
      }
      _showSnackBar(error.toString());
    } finally {
      if (mounted) {
        setState(() => _isOpeningAttachment = false);
      }
    }
  }

  Future<void> _reportConversation(AuthState authState) async {
    final accessToken = authState.session?.accessToken;
    if (accessToken == null) {
      return;
    }
    final reportsRepository = ref.read(reportsRepositoryProvider);
    final draft = await showModalBottomSheet<_ConversationReportDraft>(
      context: context,
      isScrollControlled: true,
      builder: (context) => const _ConversationReportSheet(),
    );
    if (!mounted || draft == null) {
      return;
    }
    try {
      await reportsRepository.createConversationReport(
        accessToken: accessToken,
        conversationId: widget.conversationId,
        reasonCode: draft.reasonCode,
        description: draft.description,
      );
      if (!mounted) {
        return;
      }
      _showSnackBar(
        context.tr(
          'Conversation report submitted.',
          'Жалоба на диалог отправлена.',
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      _showSnackBar(error.toString());
    }
  }

  void _markReadOnce(AuthState authState) {
    if (_didMarkRead || authState.session == null) {
      return;
    }
    _didMarkRead = true;
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) {
        return;
      }
      final token = authState.session?.accessToken;
      if (token == null) {
        return;
      }
      try {
        await ref.read(messagingRepositoryProvider).markConversationRead(
              accessToken: token,
              conversationId: widget.conversationId,
            );
        if (!mounted) {
          return;
        }
        ref.invalidate(inboxProvider);
        ref.invalidate(conversationUnreadBadgeProvider);
        ref.invalidate(notificationUnreadCountProvider);
      } catch (_) {}
    });
  }

  void _showSnackBar(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }
}

class _ConversationComposer extends StatelessWidget {
  const _ConversationComposer({
    required this.controller,
    required this.focusNode,
    required this.isSending,
    required this.pendingAttachments,
    required this.onRemoveAttachment,
    required this.onPickImage,
    required this.onPickDocument,
    required this.onSend,
  });

  final TextEditingController controller;
  final FocusNode focusNode;
  final bool isSending;
  final List<File> pendingAttachments;
  final ValueChanged<File> onRemoveAttachment;
  final Future<void> Function() onPickImage;
  final Future<void> Function() onPickDocument;
  final Future<void> Function() onSend;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 8,
      color: Theme.of(context).colorScheme.surface,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (pendingAttachments.isNotEmpty)
                SizedBox(
                  height: 44,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: pendingAttachments.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 8),
                    itemBuilder: (context, index) {
                      final file = pendingAttachments[index];
                      final isImage = _looksLikeImage(file.path);
                      return InputChip(
                        avatar: Icon(
                          isImage
                              ? Icons.image_outlined
                              : Icons.attach_file_outlined,
                        ),
                        label: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 160),
                          child: Text(
                            file.path.split(Platform.pathSeparator).last,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        onDeleted:
                            isSending ? null : () => onRemoveAttachment(file),
                      );
                    },
                  ),
                ),
              if (pendingAttachments.isNotEmpty) const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  IconButton(
                    onPressed: isSending ? null : onPickImage,
                    tooltip: context.tr('Attach image', 'Прикрепить фото'),
                    icon: const Icon(Icons.photo_library_outlined),
                  ),
                  IconButton(
                    onPressed: isSending ? null : onPickDocument,
                    tooltip:
                        context.tr('Attach document', 'Прикрепить документ'),
                    icon: const Icon(Icons.attach_file_outlined),
                  ),
                  Expanded(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxHeight: 120),
                      child: TextField(
                        controller: controller,
                        focusNode: focusNode,
                        enabled: !isSending,
                        minLines: 1,
                        maxLines: 4,
                        textInputAction: TextInputAction.newline,
                        decoration: InputDecoration(
                          hintText: context.tr(
                            'Write a message',
                            'Напишите сообщение',
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: isSending ? null : onSend,
                    tooltip: context.tr('Send', 'Отправить'),
                    icon: isSending
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.send),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  bool _looksLikeImage(String path) {
    final lower = path.toLowerCase();
    return lower.endsWith('.jpg') ||
        lower.endsWith('.jpeg') ||
        lower.endsWith('.png') ||
        lower.endsWith('.webp');
  }
}

class _ConversationReportDraft {
  const _ConversationReportDraft({
    required this.reasonCode,
    this.description,
  });

  final String reasonCode;
  final String? description;
}

class _ConversationReportSheet extends StatefulWidget {
  const _ConversationReportSheet();

  @override
  State<_ConversationReportSheet> createState() =>
      _ConversationReportSheetState();
}

class _ConversationReportSheetState extends State<_ConversationReportSheet> {
  late final TextEditingController _descriptionController;
  String _selectedReason = 'abuse';

  @override
  void initState() {
    super.initState();
    _descriptionController = TextEditingController();
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                context.tr('Report conversation', 'Пожаловаться на диалог'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _selectedReason,
                items: const [
                  DropdownMenuItem(value: 'abuse', child: Text('Abuse')),
                  DropdownMenuItem(
                      value: 'harassment', child: Text('Harassment')),
                  DropdownMenuItem(value: 'spam', child: Text('Spam')),
                  DropdownMenuItem(value: 'scam', child: Text('Scam')),
                ],
                onChanged: (value) => setState(
                  () => _selectedReason = value ?? 'abuse',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _descriptionController,
                minLines: 3,
                maxLines: 5,
                decoration: InputDecoration(
                  hintText: context.tr(
                    'Explain what happened in this conversation',
                    'Опишите, что произошло в этом диалоге',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    Navigator.of(context).pop(
                      _ConversationReportDraft(
                        reasonCode: _selectedReason,
                        description: _descriptionController.text,
                      ),
                    );
                  },
                  child: Text(
                    context.tr('Submit report', 'Отправить жалобу'),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({
    required this.message,
    required this.isMine,
    required this.accessToken,
    required this.onImageTap,
    required this.onDocumentTap,
  });

  final ConversationMessage message;
  final bool isMine;
  final String? accessToken;
  final ValueChanged<MessageAttachment> onImageTap;
  final ValueChanged<MessageAttachment> onDocumentTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final bubbleColor =
        isMine ? colorScheme.primaryContainer : colorScheme.surfaceContainer;

    return Align(
      alignment: isMine ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 320),
        child: Card(
          color: bubbleColor,
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment:
                  isMine ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                if ((message.body ?? '').isNotEmpty) Text(message.body!),
                if (message.attachments.isNotEmpty) ...[
                  if ((message.body ?? '').isNotEmpty)
                    const SizedBox(height: 8),
                  ...message.attachments.map(
                    (attachment) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: attachment.isImage
                          ? InkWell(
                              onTap: () => onImageTap(attachment),
                              borderRadius: BorderRadius.circular(12),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  NetworkMediaImage(
                                    requestPath: attachment.downloadUrl,
                                    accessToken: accessToken,
                                    width: 220,
                                    height: 160,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    attachment.fileName,
                                    style:
                                        Theme.of(context).textTheme.bodySmall,
                                  ),
                                ],
                              ),
                            )
                          : InkWell(
                              onTap: () => onDocumentTap(attachment),
                              borderRadius: BorderRadius.circular(12),
                              child: Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .outlineVariant,
                                  ),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.description_outlined),
                                    const SizedBox(width: 8),
                                    Flexible(
                                      child: Text(
                                        attachment.fileName,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                    ),
                  ),
                ],
                const SizedBox(height: 4),
                Text(
                  DateFormat('MMM d, HH:mm')
                      .format(message.createdAt.toLocal()),
                  style: Theme.of(context).textTheme.labelSmall,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AttachmentImageViewer extends StatelessWidget {
  const _AttachmentImageViewer({
    required this.title,
    required this.requestPath,
    required this.accessToken,
  });

  final String title;
  final String requestPath;
  final String accessToken;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: InteractiveViewer(
        minScale: 0.8,
        maxScale: 4,
        child: Center(
          child: NetworkMediaImage(
            requestPath: requestPath,
            accessToken: accessToken,
            fit: BoxFit.contain,
            width: double.infinity,
            height: double.infinity,
          ),
        ),
      ),
    );
  }
}
