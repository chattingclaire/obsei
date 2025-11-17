'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

export default function PipelineMetrics() {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('http://localhost:8000/metrics/pipeline');
        setMetrics(response.data);
      } catch (error) {
        console.error('获取指标失败:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, []);

  if (!metrics) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-4 border border-gray-700">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
          <div className="space-y-2">
            <div className="h-12 bg-gray-700 rounded"></div>
            <div className="h-12 bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const metricsData = [
    {
      label: '原始数据',
      value: metrics.raw_items || 0,
      icon: '📥',
      color: 'text-blue-400'
    },
    {
      label: '已分类',
      value: metrics.classified_items || 0,
      icon: '🏷️',
      color: 'text-green-400'
    },
    {
      label: '信号',
      value: metrics.signals || 0,
      icon: '📡',
      color: 'text-purple-400'
    },
    {
      label: '洞察',
      value: metrics.insights || 0,
      icon: '💡',
      color: 'text-yellow-400'
    },
    {
      label: '投资机会',
      value: metrics.investments || 0,
      icon: '💼',
      color: 'text-pink-400'
    }
  ];

  return (
    <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-4 border border-gray-700">
      <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
        <span className="text-xl">📊</span>
        知识库统计
      </h2>

      <div className="space-y-2">
        {metricsData.map((metric) => (
          <div
            key={metric.label}
            className="bg-gray-700/50 rounded-lg p-3 flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <span className="text-xl">{metric.icon}</span>
              <span className="text-sm text-gray-300">{metric.label}</span>
            </div>
            <span className={`text-lg font-bold ${metric.color}`}>
              {metric.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-gray-700">
        <div className="text-xs text-gray-400 text-center">
          最后更新: {new Date(metrics.timestamp || Date.now()).toLocaleTimeString('zh-CN')}
        </div>
      </div>
    </div>
  );
}
