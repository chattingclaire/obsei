'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface AgentChatProps {
  agentName: string;
  agentInfo: any;
}

export default function AgentChat({ agentName, agentInfo }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [autoQueryKB, setAutoQueryKB] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    // Load chat history when agent changes
    loadChatHistory();
  }, [agentName]);

  useEffect(() => {
    // Scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/chat/${agentName}/history`);
      if (response.data.history) {
        setMessages(response.data.history);
      }
    } catch (error) {
      console.error('加载聊天历史失败:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');

    // Add user message to UI
    const newUserMessage: Message = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/chat/${agentName}`, {
        message: userMessage,
        agent_name: agentName,
        auto_query_kb: autoQueryKB
      });

      if (response.data.success) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.data.message,
          timestamp: response.data.timestamp
        };

        setMessages(prev => [...prev, assistantMessage]);

        // Handle special responses (signals, recommendations, etc.)
        if (response.data.generated_signals) {
          console.log('生成的信号:', response.data.generated_signals);
        }
        if (response.data.recommendations) {
          console.log('推荐:', response.data.recommendations);
        }
      } else {
        throw new Error(response.data.error || '请求失败');
      }
    } catch (error: any) {
      console.error('发送消息失败:', error);

      const errorMessage: Message = {
        role: 'assistant',
        content: `抱歉，处理您的请求时出现错误: ${error.message}`,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = async () => {
    if (confirm('确定要清空聊天记录吗？')) {
      try {
        await axios.delete(`${API_BASE}/chat/${agentName}/history`);
        setMessages([]);
      } catch (error) {
        console.error('清空历史失败:', error);
      }
    }
  };

  const quickPrompts = {
    signal_agent: [
      '帮我查找最近的AI创业项目',
      '生成一个关于Web3的信号',
      '有哪些中国创始人的项目？'
    ],
    insight_agent: [
      '分析最近一周的趋势',
      '哪些类别最热门？',
      '生成本周投资洞察报告'
    ],
    venture_agent: [
      '推荐高分投资机会',
      '分析中国创始人的项目',
      '查找AI领域的种子轮项目'
    ]
  };

  const prompts = quickPrompts[agentName as keyof typeof quickPrompts] || [];

  return (
    <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl border border-gray-700 overflow-hidden flex flex-col h-[calc(100vh-200px)]">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center text-2xl">
              {agentInfo?.name === 'signal_agent' && '📡'}
              {agentInfo?.name === 'insight_agent' && '💡'}
              {agentInfo?.name === 'venture_agent' && '💼'}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                {agentInfo?.display_name || agentName}
              </h2>
              <p className="text-sm text-blue-100">
                {agentInfo?.description}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm text-white cursor-pointer">
              <input
                type="checkbox"
                checked={autoQueryKB}
                onChange={(e) => setAutoQueryKB(e.target.checked)}
                className="rounded"
              />
              自动查询知识库
            </label>

            <button
              onClick={clearHistory}
              className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-white text-sm transition-colors"
            >
              清空历史
            </button>
          </div>
        </div>

        {/* Capabilities */}
        {agentInfo?.capabilities && (
          <div className="mt-3 flex flex-wrap gap-2">
            {agentInfo.capabilities.map((cap: string) => (
              <span
                key={cap}
                className="px-2 py-1 bg-white/10 rounded-full text-xs text-white"
              >
                {cap}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-8">
            <p className="text-lg mb-4">👋 开始与 {agentInfo?.display_name} 对话</p>
            <div className="space-y-2">
              <p className="text-sm">试试这些快捷提示:</p>
              <div className="flex flex-wrap gap-2 justify-center mt-2">
                {prompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInputMessage(prompt)}
                    className="px-3 py-2 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg text-sm text-gray-300 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((message, idx) => (
          <div
            key={idx}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              <div className="whitespace-pre-wrap break-words">
                {message.content}
              </div>
              <div
                className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                }`}
              >
                {new Date(message.timestamp).toLocaleTimeString('zh-CN')}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce delay-200"></div>
                <span className="text-gray-300 text-sm ml-2">正在思考...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-700 bg-gray-800/70">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="输入您的问题..."
            className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
          >
            {isLoading ? '发送中...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  );
}
