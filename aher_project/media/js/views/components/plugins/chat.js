define([
    'knockout',
    'jquery',
    'arches',
    'templates/views/components/plugins/chat.htm'
], function(ko, $, arches, chatPluginTemplate) {
    return ko.components.register('chat', {
        viewModel: function(params) {
            var self = this;
            this.ready = ko.observable(false);
            this.messages = ko.observableArray([]);
            this.userInput = ko.observable('');
            this.loading = ko.observable(false);

            this.canSend = ko.computed(function() {
                return !self.loading() && self.userInput().trim() !== '';
            });

            // Auto-grow textarea
            this.autoGrowTextarea = function(data, event) {
                const textarea = event.target;
                textarea.style.height = 'auto';
                const newHeight = Math.min(textarea.scrollHeight, 200);
                textarea.style.height = newHeight + 'px';
            };

            // Scroll to bottom of messages with smooth scrolling for non-reduced-motion users
            this.scrollToBottom = function() {
                setTimeout(function() {
                    const messagesDiv = document.querySelector('.chat-messages');
                    if (messagesDiv) {
                        const shouldAnimate = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                        messagesDiv.scrollTo({
                            top: messagesDiv.scrollHeight,
                            behavior: shouldAnimate ? 'smooth' : 'auto'
                        });
                    }
                }, 0);
            };

            // Subscribe to messages changes to auto-scroll
            this.messages.subscribe(this.scrollToBottom);

            // Enhanced keyboard navigation
            this.handleKeyPress = function(data, event) {
                self.autoGrowTextarea(data, event);
                
                // Send message on Enter (without shift)
                if (event.keyCode === 13 && !event.shiftKey) {
                    self.sendMessage();
                    return false;
                }
                return true;
            };

            this.sendMessage = function() {
                if (!self.canSend()) return;

                const userMessage = self.userInput().trim();
                if (!userMessage) return;

                self.loading(true);
                
                // Add user message to chat and announce to screen readers
                self.messages.push({
                    role: 'user',
                    content: userMessage
                });

                // Clear input and reset height
                self.userInput('');
                const textarea = document.querySelector('.chat-input textarea');
                if (textarea) {
                    textarea.style.height = '44px'; // Reset to minimum height
                    textarea.focus(); // Keep focus on textarea after sending
                }

                // Prepare messages for API
                const messageHistory = self.messages().map(m => ({
                    role: m.role,
                    content: m.content
                }));

                // Send to backend
                $.ajax({
                    url: arches.urls.root + 'chatapi/',
                    type: 'POST',
                    data: JSON.stringify({
                        messages: messageHistory
                    }),
                    contentType: 'application/json',
                    success: function(response) {
                        if (response && response.response) {
                            self.messages.push({
                                role: 'assistant',
                                content: response.response
                            });
                        }
                    },
                    error: function(err) {
                        console.error('Chat error:', err);
                        self.messages.push({
                            role: 'assistant',
                            content: 'Sorry, there was an error processing your request.'
                        });
                    },
                    complete: function() {
                        self.loading(false);
                    }
                });
            };

            this.confirmClearChat = function() {
                if (self.messages().length === 0) return;
                
                if (confirm('Are you sure you want to clear the chat history? This action cannot be undone.')) {
                    self.messages.removeAll();
                    // Focus back on textarea after clearing
                    const textarea = document.querySelector('.chat-input textarea');
                    if (textarea) {
                        textarea.focus();
                    }
                }
            };

            // Initialize
            this.ready(true);

            // Focus textarea on component load
            setTimeout(function() {
                const textarea = document.querySelector('.chat-input textarea');
                if (textarea) {
                    textarea.focus();
                }
            }, 0);
        },
        template: chatPluginTemplate
    });
});