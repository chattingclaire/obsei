'use client';

import { useState, useEffect } from 'react';
import AgentChat from '@/components/AgentChat';
import AgentSelector from '@/components/AgentSelector';
import AgentStatus from '@/components/AgentStatus';
import PipelineMetrics from '@/components/PipelineMetrics';

export default function Home() {
  const [selectedAgent, setSelectedAgent] = useState('signal_agent');
  const [agents, setAgents] = useState([]);
  const [agentStatuses, setAgentStatuses] = useState({});

  useEffect(() => {
    // Fetch agents list
    fetch('http://localhost:8000/agents/list')
      .then(res => res.json())
      .then(data => setAgents(data.agents))
      .catch(console.error);

    // Fetch agent statuses
    const fetchStatuses = () => {
      fetch('http://localhost:8000/agents/status')
        .then(res => res.json())
        .then(data => {
          const statusMap = {};
          data.forEach(agent => {
            statusMap[agent.agent_name] = agent;
          });
          setAgentStatuses(statusMap);
        })
        .catch(console.error);
    };

    fetchStatuses();
    const interval = setInterval(fetchStatuses, 10000); // Update every 10s

    return () => clearInterval(interval);
  }, []);

  const chatAgents = agents.filter(a => a.chat_enabled);
  const backgroundAgents = agents.filter(a => !a.chat_enabled);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      {/* Header */}
      <div className="bg-gray-800/50 backdrop-blur-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <span className="text-4xl">🤖</span>
            多Agent智能平台
          </h1>
          <p className="text-gray-400 mt-1">
            与AI Agents对话，获取实时洞察和投资分析
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Agent Selector & Status */}
          <div className="lg:col-span-1 space-y-4">
            {/* Background Agents Status */}
            <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-4 border border-gray-700">
              <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                后台Agents
              </h2>
              <div className="space-y-2">
                {backgroundAgents.map(agent => (
                  <div
                    key={agent.name}
                    className="bg-gray-700/50 rounded-lg p-3 border border-gray-600"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-white">
                        {agent.display_name}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        agentStatuses[agent.name]?.status === 'running'
                          ? 'bg-green-500/20 text-green-300'
                          : 'bg-gray-500/20 text-gray-300'
                      }`}>
                        {agentStatuses[agent.name]?.status || 'idle'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">{agent.description}</p>
                    {agentStatuses[agent.name] && (
                      <div className="mt-2 text-xs text-gray-500">
                        处理: {agentStatuses[agent.name].processed_count || 0} 项
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Chat Agents Selector */}
            <AgentSelector
              agents={chatAgents}
              selectedAgent={selectedAgent}
              onSelectAgent={setSelectedAgent}
              agentStatuses={agentStatuses}
            />

            {/* Pipeline Metrics */}
            <PipelineMetrics />
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-3">
            {selectedAgent && (
              <AgentChat
                agentName={selectedAgent}
                agentInfo={agents.find(a => a.name === selectedAgent)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
