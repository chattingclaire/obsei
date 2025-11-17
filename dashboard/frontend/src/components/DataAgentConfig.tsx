'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface DataSource {
  name: string;
  enabled: boolean;
  config: {
    accounts?: string[];
    keywords?: string[];
    max_results?: number;
  };
}

export default function DataAgentConfig() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [newAccount, setNewAccount] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE}/config/data_agent`);
      if (response.data.sources) {
        const sourcesArray = Object.entries(response.data.sources).map(([name, config]: [string, any]) => ({
          name,
          enabled: config.enabled || false,
          config: config
        }));
        setSources(sourcesArray);
      }
    } catch (error) {
      console.error('加载配置失败:', error);
    }
  };

  const toggleSource = async (sourceName: string) => {
    try {
      const updatedSources = sources.map(s =>
        s.name === sourceName ? { ...s, enabled: !s.enabled } : s
      );
      setSources(updatedSources);

      await axios.put(`${API_BASE}/config/data_agent/sources/${sourceName}`, {
        enabled: !sources.find(s => s.name === sourceName)?.enabled
      });
    } catch (error) {
      console.error('更新失败:', error);
      loadConfig(); // Reload on error
    }
  };

  const addAccount = async () => {
    if (!selectedSource || !newAccount.trim()) return;

    try {
      const source = sources.find(s => s.name === selectedSource);
      if (!source) return;

      const updatedAccounts = [...(source.config.accounts || []), newAccount.trim()];

      await axios.post(`${API_BASE}/config/data_agent/sources/${selectedSource}/accounts`, {
        account: newAccount.trim()
      });

      setNewAccount('');
      loadConfig();
    } catch (error) {
      console.error('添加账号失败:', error);
    }
  };

  const removeAccount = async (sourceName: string, account: string) => {
    try {
      await axios.delete(`${API_BASE}/config/data_agent/sources/${sourceName}/accounts/${encodeURIComponent(account)}`);
      loadConfig();
    } catch (error) {
      console.error('删除账号失败:', error);
    }
  };

  const sourceIcons: {[key: string]: string} = {
    'github': '🐙',
    'twitter': '🐦',
    'reddit': '🤖',
    'producthunt': '🚀',
    'hackernews': '📰',
    'youtube': '📺',
    'techcrunch': '📱',
    'kickstarter': '💰',
    'crunchbase': '💼'
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
      <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
        <span className="text-3xl">📥</span>
        Data Agent 信息源配置
      </h2>

      <div className="space-y-4">
        {/* Sources List */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sources.map((source) => (
            <div
              key={source.name}
              className="bg-gray-700/50 rounded-lg p-4 border border-gray-600"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{sourceIcons[source.name] || '📡'}</span>
                  <h3 className="text-lg font-semibold text-white capitalize">
                    {source.name}
                  </h3>
                </div>

                <button
                  onClick={() => toggleSource(source.name)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    source.enabled
                      ? 'bg-green-500/20 text-green-300 hover:bg-green-500/30'
                      : 'bg-gray-500/20 text-gray-400 hover:bg-gray-500/30'
                  }`}
                >
                  {source.enabled ? '已启用' : '已禁用'}
                </button>
              </div>

              {/* Accounts */}
              {source.config.accounts && source.config.accounts.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-400 mb-2">固定账号:</p>
                  <div className="flex flex-wrap gap-2">
                    {source.config.accounts.map((account) => (
                      <div
                        key={account}
                        className="flex items-center gap-1 px-2 py-1 bg-blue-500/20 rounded-full text-xs text-blue-300"
                      >
                        <span>{account}</span>
                        <button
                          onClick={() => removeAccount(source.name, account)}
                          className="hover:text-red-400 transition-colors"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Keywords */}
              {source.config.keywords && source.config.keywords.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-400 mb-2">关键词:</p>
                  <div className="flex flex-wrap gap-2">
                    {source.config.keywords.slice(0, 5).map((keyword) => (
                      <span
                        key={keyword}
                        className="px-2 py-1 bg-purple-500/20 rounded-full text-xs text-purple-300"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Max Results */}
              <div className="mt-3 text-xs text-gray-500">
                最大结果数: {source.config.max_results || 50}
              </div>
            </div>
          ))}
        </div>

        {/* Add Account Section */}
        <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-4 border border-blue-500/30">
          <h3 className="text-lg font-semibold text-white mb-3">添加固定账号</h3>

          <div className="flex gap-3">
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">选择信息源...</option>
              {sources.map((source) => (
                <option key={source.name} value={source.name}>
                  {sourceIcons[source.name]} {source.name.charAt(0).toUpperCase() + source.name.slice(1)}
                </option>
              ))}
            </select>

            <input
              type="text"
              value={newAccount}
              onChange={(e) => setNewAccount(e.target.value)}
              placeholder="账号名称或URL..."
              className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            <button
              onClick={addAccount}
              disabled={!selectedSource || !newAccount.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
            >
              添加
            </button>
          </div>

          <div className="mt-3 text-sm text-gray-400">
            💡 提示: 添加Twitter账号、GitHub用户、Reddit subreddits等，系统会持续跟踪这些账号
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={loadConfig}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white font-medium transition-colors"
          >
            刷新配置
          </button>
        </div>
      </div>
    </div>
  );
}
