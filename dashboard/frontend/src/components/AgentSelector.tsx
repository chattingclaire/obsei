'use client';

interface Agent {
  name: string;
  display_name: string;
  description: string;
  chat_enabled: boolean;
  capabilities?: string[];
}

interface AgentSelectorProps {
  agents: Agent[];
  selectedAgent: string;
  onSelectAgent: (agentName: string) => void;
  agentStatuses: any;
}

export default function AgentSelector({
  agents,
  selectedAgent,
  onSelectAgent,
  agentStatuses
}: AgentSelectorProps) {
  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case 'signal_agent':
        return '📡';
      case 'insight_agent':
        return '💡';
      case 'venture_agent':
        return '💼';
      default:
        return '🤖';
    }
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-4 border border-gray-700">
      <h2 className="text-lg font-semibold text-white mb-3">对话Agents</h2>

      <div className="space-y-2">
        {agents.map((agent) => (
          <button
            key={agent.name}
            onClick={() => onSelectAgent(agent.name)}
            className={`w-full text-left p-3 rounded-lg transition-all ${
              selectedAgent === agent.name
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg scale-105'
                : 'bg-gray-700/50 hover:bg-gray-600/50 text-gray-300 hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{getAgentIcon(agent.name)}</span>
              <div className="flex-1">
                <div className="font-medium">{agent.display_name}</div>
                <div className="text-xs opacity-75 mt-0.5">
                  {agent.description}
                </div>
              </div>

              {selectedAgent === agent.name && (
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>
          </button>
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-2 text-sm text-blue-300">
          <span className="text-lg">💡</span>
          <div>
            <p className="font-medium mb-1">提示</p>
            <p className="text-xs text-blue-200/80">
              选择一个Agent开始对话。它们可以访问知识库并使用各种工具来帮助您。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
