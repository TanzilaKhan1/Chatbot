'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  chatWithSession, 
  getFolderSessions, 
  getSession, 
  deleteSession,
  updateSessionTitle 
} from '../services/api';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarProvider,
  useSidebar,
} from '../components/ui/sidebar';
import { 
  PlusIcon, 
  ArrowUpIcon, 
  PaperclipIcon, 
  ChevronDownIcon, 
  GlobeIcon, 
  LockIcon,
  UserIcon,
  TrashIcon 
} from '../components/icons';
import { nanoid } from 'nanoid';
import { cn } from '../lib/utils';
import Link from 'next/link';
import React from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const Greeting = () => {
  return (
    <div className="max-w-3xl mx-auto md:mt-20 px-8 size-full flex flex-col justify-center">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 10 }}
        transition={{ delay: 0.5 }}
        className="text-2xl font-semibold"
      >
        Hello there!
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 10 }}
        transition={{ delay: 0.6 }}
        className="text-2xl text-zinc-500"
      >
        How can I help you today?
      </motion.div>
    </div>
  );
};

const SuggestedActions = ({ onSuggestionClick }: { onSuggestionClick: (content: string) => void }) => {
  const suggestedActions = [
    {
      title: 'What are the advantages',
      label: 'of using Next.js?',
      action: 'What are the advantages of using Next.js?',
    },
    {
      title: 'Write code to',
      label: `demonstrate djikstra's algorithm`,
      action: `Write code to demonstrate djikstra's algorithm`,
    },
    {
      title: 'Help me write an essay',
      label: `about silicon valley`,
      action: `Help me write an essay about silicon valley`,
    },
    {
      title: 'What is the weather',
      label: 'in San Francisco?',
      action: 'What is the weather in San Francisco?',
    },
  ];

  return (
    <div className="grid sm:grid-cols-2 gap-2 w-full">
      {suggestedActions.map((suggestedAction, index) => (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ delay: 0.05 * index }}
          key={`suggested-action-${suggestedAction.title}-${index}`}
          className={index > 1 ? 'hidden sm:block' : 'block'}
        >
          <Button
            variant="ghost"
            onClick={() => onSuggestionClick(suggestedAction.action)}
            className="text-left border rounded-xl px-4 py-3.5 text-sm flex-1 gap-1 sm:flex-col w-full h-auto justify-start items-start"
          >
            <span className="font-medium">{suggestedAction.title}</span>
            <span className="text-muted-foreground">
              {suggestedAction.label}
            </span>
          </Button>
        </motion.div>
      ))}
    </div>
  );
};

const AppSidebar = ({ 
  chatHistory, 
  onNewChat, 
  activeChatId,
  onSelectChat,
  onDeleteChat,
  isLoadingHistory
}: { 
  chatHistory: Array<{ id: string, title: string }>, 
  onNewChat: () => void,
  activeChatId: string | null,
  onSelectChat: (chatId: string) => void,
  onDeleteChat: (chatId: string) => void,
  isLoadingHistory: boolean
}) => {
  const router = useRouter();
  const { setOpenMobile } = useSidebar();

  const handleChatClick = (chatId: string) => {
    onSelectChat(chatId);
    setOpenMobile(false);
  };

  return (
    <Sidebar className="group-data-[side=left]:border-r-0">
      <SidebarHeader>
        <SidebarMenu>
          <div className="flex flex-row justify-between items-center">
            <div
              onClick={() => {
                onNewChat();
                setOpenMobile(false);
              }}
              className="flex flex-row gap-3 items-center"
            >
              <span className="text-lg font-semibold px-2 hover:bg-muted rounded-md cursor-pointer">
                Chatbot
              </span>
            </div>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    type="button"
                    className="p-2 h-fit"
                    onClick={() => {
                      setOpenMobile(false);
                      onNewChat();
                    }}
                  >
                    <PlusIcon />
                  </Button>
                </TooltipTrigger>
                <TooltipContent align="end">New Chat</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <div className="flex flex-col gap-2 p-2">
          {isLoadingHistory ? (
            <div className="text-xs text-zinc-500 px-2 py-1">Loading chat history...</div>
          ) : (
            <>
              {chatHistory.length > 0 && <div className="text-xs text-zinc-500 px-2 py-1">Recent Chats</div>}
              {chatHistory.map((item) => (
                <div
                  key={item.id}
                  className={`flex items-center gap-2 px-2 py-2 text-sm hover:bg-accent rounded-md cursor-pointer group ${
                    activeChatId === item.id ? 'bg-accent' : ''
                  }`}
                  onClick={() => handleChatClick(item.id)}
                >
                  <span className="truncate flex-1">{item.title}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 p-1 h-fit"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteChat(item.id);
                    }}
                  >
                    <TrashIcon size={14} />
                  </Button>
                </div>
              ))}
              {chatHistory.length > 0 && (
                <div className="text-xs text-zinc-500 px-2 py-1 mt-4">
                  You have reached the end of your chat history.
                </div>
              )}
            </>
          )}
        </div>
      </SidebarContent>
      <SidebarFooter>
        <div className="flex items-center gap-2 px-2 py-2">
          <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
            <UserIcon />
          </div>
          <span className="text-sm font-medium">Guest</span>
          <ChevronDownIcon className="ml-auto" />
        </div>
      </SidebarFooter>
    </Sidebar>
  );
};

const MultimodalInput = ({ 
  input, 
  setInput, 
  onSubmit, 
  isLoading, 
  showSuggestions 
}: {
  input: string;
  setInput: (value: string) => void;
  onSubmit: (content: string) => void;
  isLoading: boolean;
  showSuggestions: boolean;
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSubmit(input);
  };

  return (
    <div className="relative w-full flex flex-col gap-4">
      {showSuggestions && (
        <SuggestedActions onSuggestionClick={(content) => onSubmit(content)} />
      )}

      <div className="relative">
        <Textarea
          placeholder="Send a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className={cn(
            'min-h-[24px] max-h-[calc(75dvh)] overflow-hidden resize-none rounded-2xl !text-base bg-muted pb-10 dark:border-zinc-700',
          )}
          rows={2}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              handleSubmit(event);
            }
          }}
        />

        <div className="absolute bottom-0 p-2 w-fit flex flex-row justify-start">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  className="rounded-md p-[7px] h-fit dark:border-zinc-700 hover:dark:bg-zinc-900 hover:bg-zinc-200"
                  disabled={isLoading}
                  variant="ghost"
                >
                  <PaperclipIcon size={14} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Attach files</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className="absolute bottom-0 right-0 p-2 w-fit flex flex-row justify-end">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  className="rounded-full p-1.5 h-fit border dark:border-zinc-600"
                  onClick={handleSubmit}
                  disabled={input.length === 0 || isLoading}
                >
                  <ArrowUpIcon size={14} />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Send message</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    </div>
  );
};

const ChatHeader = ({ selectedModel, setSelectedModel }: { 
  selectedModel: string;
  setSelectedModel: (model: string) => void;
}) => {
  const { toggleSidebar } = useSidebar();
  const router = useRouter();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleBackClick = () => {
    router.push('/');
  };

  return (
    <div className="flex items-center justify-between p-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center gap-2">
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={toggleSidebar} 
          className="p-2 h-fit"
        >
          <svg
            width="15"
            height="15"
            viewBox="0 0 15 15"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-4 h-4"
          >
            <path
              d="M1.5 3C1.22386 3 1 3.22386 1 3.5C1 3.77614 1.22386 4 1.5 4H13.5C13.7761 4 14 3.77614 14 3.5C14 3.22386 13.7761 3 13.5 3H1.5ZM1.5 7.5C1.22386 7.5 1 7.72386 1 8C1 8.27614 1.22386 8.5 1.5 8.5H13.5C13.7761 8.5 14 8.27614 14 8C14 7.72386 13.7761 7.5 13.5 7.5H1.5ZM1.5 12C1.22386 12 1 12.2239 1 12.5C1 12.7761 1.22386 13 1.5 13H13.5C13.7761 13 14 12.7761 14 12.5C14 12.2239 13.7761 12 13.5 12H1.5Z"
              fill="currentColor"
              fillRule="evenodd"
              clipRule="evenodd"
            ></path>
          </svg>
        </Button>
        <div className="relative" ref={dropdownRef}>
          <Button 
            variant="ghost" 
            size="sm" 
            className={`gap-2 ${selectedModel === 'Simple' ? 'text-amber-600' : ''}`}
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          >
            <span className="font-semibold">
              {selectedModel === 'OpenAI' && (
                <>Chat model: OpenAI</>
              )}
              {selectedModel === 'Simple' && (
                <>Simple chat mode</>
              )}
              {selectedModel !== 'OpenAI' && selectedModel !== 'Simple' && (
                <>Chat model: {selectedModel}</>
              )}
            </span>
            <ChevronDownIcon size={16} />
          </Button>
          {isDropdownOpen && (
            <div className="absolute top-full left-0 mt-1 bg-popover shadow-md rounded-md border border-border z-10">
              <div className="py-1">
                <button 
                  className="w-full text-left px-4 py-2 hover:bg-accent text-sm"
                  onClick={() => {
                    setSelectedModel('OpenAI');
                    setIsDropdownOpen(false);
                  }}
                >
                  OpenAI
                </button>
                <button 
                  className="w-full text-left px-4 py-2 hover:bg-accent text-sm"
                  onClick={() => {
                    setSelectedModel('Simple');
                    setIsDropdownOpen(false);
                  }}
                >
                  Simple Mode
                </button>
              </div>
            </div>
          )}
        </div>
        {selectedModel === 'Simple' && (
          <span className="text-xs text-amber-600 bg-amber-100 px-2 py-1 rounded-md">
            Using local embeddings (fallback mode)
          </span>
        )}
      </div>
      <div className="flex items-center">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="default"
                onClick={handleBackClick}
                className="bg-black text-white hover:bg-black/90 h-9"
                aria-label="Back to files"
              >
                Back
              </Button>
            </TooltipTrigger>
            <TooltipContent>Back to files</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  );
};

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<Array<{ id: string, title: string }>>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState('OpenAI');
  const [isSmallScreen, setIsSmallScreen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [folderId, setFolderId] = useState<string | null>(null);
  
  // Get folder ID from URL params
  useEffect(() => {
    const folderIdParam = searchParams.get('folder_id');
    console.log('Folder ID from URL:', folderIdParam); // Debug log
    
    if (folderIdParam && folderIdParam !== 'null' && folderIdParam.trim() !== '') {
      setFolderId(folderIdParam);
      loadFolderSessions(folderIdParam);
    } else {
      // If no valid folder_id, redirect to home page
      console.log('Invalid or missing folder_id, redirecting to home');
      router.push('/');
    }
  }, [searchParams, router]);

  // Load folder sessions
  const loadFolderSessions = async (folderId: string) => {
    // Validate folder ID before making API call
    if (!folderId || folderId === 'null' || folderId.trim() === '') {
      console.error('Invalid folder ID provided to loadFolderSessions:', folderId);
      setError('Invalid folder ID');
      return;
    }
    
    try {
      setIsLoadingHistory(true);
      const sessions = await getFolderSessions(folderId);
      setChatHistory(sessions.map(s => ({ id: s.id, title: s.title })));
      
      // Check if there's a session ID in the URL
      const sessionId = searchParams.get('id');
      if (sessionId) {
        await loadChatById(sessionId);
      }
    } catch (error) {
      console.error("Failed to load sessions:", error);
      setError("Failed to load chat history.");
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Load chat by its ID
  const loadChatById = async (sessionId: string) => {
    try {
      setError(null);
      setActiveChatId(sessionId);
      
      const session = await getSession(sessionId);
      setMessages(session.messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.created_at)
      })));
      setSelectedModel(session.model || 'OpenAI');
      
      // Update URL - ensure folderId is valid
      if (folderId && folderId !== 'null') {
        const newUrl = `/chat?folder_id=${folderId}&id=${sessionId}`;
        window.history.pushState({}, '', newUrl);
      }
    } catch (error) {
      console.error("Failed to load chat messages:", error);
      setError("Failed to load this chat.");
      setMessages([]);
    }
  };
  
  // Check if screen is small
  useEffect(() => {
    const checkScreenSize = () => {
      setIsSmallScreen(window.innerWidth < 768);
    };
    
    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  const createNewChat = () => {
    setMessages([]);
    setActiveChatId(null);
    
    // Update URL without session ID - ensure folderId is valid
    if (folderId && folderId !== 'null') {
      const newUrl = `/chat?folder_id=${folderId}`;
      window.history.pushState({}, '', newUrl);
    }
  };

  const handleDeleteChat = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      
      // Remove from chat history
      setChatHistory(prev => prev.filter(chat => chat.id !== sessionId));
      
      // If this was the active chat, clear it
      if (activeChatId === sessionId) {
        createNewChat();
      }
    } catch (error) {
      console.error("Failed to delete chat:", error);
      setError("Failed to delete chat.");
    }
  };

  const handleSubmit = async (content: string) => {
    // Validate inputs before proceeding
    if (!content.trim() || isLoading) return;
    
    if (!folderId || folderId === 'null' || folderId.trim() === '') {
      console.error('Cannot submit chat without valid folder ID:', folderId);
      setError('Invalid folder selected. Please go back and select a valid folder.');
      return;
    }

    const userMessage: Message = {
      id: nanoid(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatWithSession(
        content.trim(),
        folderId,
        activeChatId || undefined,
        selectedModel
      );

      // If we got a response but the model is different, it means we fell back to simple mode
      const usedFallback = selectedModel === 'OpenAI' && response.model === 'Simple';
      if (usedFallback) {
        // Add a system notification about fallback
        const fallbackNotice: Message = {
          id: nanoid(),
          role: 'assistant',
          content: 'OpenAI API quota exceeded. Automatically switched to simple chat mode for this response.',
          timestamp: new Date(),
        };
        updatedMessages.push(fallbackNotice);
      }

      const aiMessage: Message = {
        id: nanoid(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      
      const finalMessages = [...updatedMessages, aiMessage];
      setMessages(finalMessages);
      
      // If fallback occurred, update the selected model in the UI
      if (usedFallback) {
        setSelectedModel('Simple');
      }
      
      // Update active chat ID if this created a new session
      if (!activeChatId && response.session_id) {
        setActiveChatId(response.session_id);
        // Reload sessions to show the new one
        await loadFolderSessions(folderId);
      }
      
    } catch (error) {
      console.error('Chat API error:', error);
      
      const errorMessage: Message = {
        id: nanoid(),
        role: 'assistant',
        content: 'I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      
      setMessages([...updatedMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const showSuggestions = messages.length === 0;

  // Show loading state while checking for folder ID
  if (folderId === null) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // This should not be reached anymore since we redirect in useEffect
  if (!folderId || folderId === 'null') {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-4">No folder selected</h2>
          <p className="text-muted-foreground mb-4">
            Please select a folder from the main page to start chatting with your documents.
          </p>
          <Button onClick={() => router.push('/')}>
            Go to Folders
          </Button>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <SidebarProvider defaultOpen={!isSmallScreen}>
        <AppSidebar 
          chatHistory={chatHistory}
          onNewChat={createNewChat}
          activeChatId={activeChatId}
          onSelectChat={loadChatById}
          onDeleteChat={handleDeleteChat}
          isLoadingHistory={isLoadingHistory}
        />
        <SidebarInset className="flex flex-col h-screen">
          <ChatHeader 
            selectedModel={selectedModel}
            setSelectedModel={setSelectedModel}
          />
          
          <div className="flex-1 flex flex-col min-h-0">
            {/* Messages area */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden">
              {error ? (
                <div className="max-w-3xl mx-auto mt-8 p-4 bg-red-50 text-red-800 rounded-md">
                  <p className="font-medium">Error</p>
                  <p>{error}</p>
                  <Button 
                    onClick={() => {
                      setError(null);
                      createNewChat();
                    }}
                    className="mt-2"
                  >
                    Start New Chat
                  </Button>
                </div>
              ) : messages.length === 0 ? (
                <Greeting />
              ) : (
                <div className="max-w-3xl mx-auto p-4 space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`w-full max-w-xs sm:max-w-md lg:max-w-lg xl:max-w-xl px-4 py-2 rounded-lg overflow-x-hidden ${
                          message.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        <p className="text-sm message-content">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-muted text-muted-foreground px-4 py-2 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                            <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          </div>
                          <span className="text-xs">AI is typing...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Input area - Fixed at bottom */}
            <div className="flex-shrink-0 border-t bg-background p-4">
              <div className="max-w-3xl mx-auto">
                <MultimodalInput
                  input={input}
                  setInput={setInput}
                  onSubmit={handleSubmit}
                  isLoading={isLoading}
                  showSuggestions={showSuggestions}
                />
              </div>
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  );
}