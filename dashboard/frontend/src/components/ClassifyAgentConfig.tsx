'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface TaxonomyCategory {
  label: string;
  code: string;
  description: string;
  subcategories?: {[key: string]: TaxonomyCategory};
}

interface CustomField {
  name: string;
  type: string;
  required: boolean;
  options?: string[];
}

export default function ClassifyAgentConfig() {
  const [taxonomy, setTaxonomy] = useState<{[key: string]: TaxonomyCategory}>({});
  const [customFields, setCustomFields] = useState<CustomField[]>([]);
  const [newField, setNewField] = useState<CustomField>({
    name: '',
    type: 'text',
    required: false
  });
  const [selectedL1, setSelectedL1] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      // Load taxonomy
      const taxonomyRes = await axios.get(`${API_BASE}/config/taxonomy`);
      if (taxonomyRes.data.categories) {
        setTaxonomy(taxonomyRes.data.categories);
      }

      // Load custom fields
      const fieldsRes = await axios.get(`${API_BASE}/config/classify_agent/custom_fields`);
      if (fieldsRes.data.fields) {
        setCustomFields(fieldsRes.data.fields);
      }
    } catch (error) {
      console.error('加载配置失败:', error);
    }
  };

  const addCustomField = async () => {
    if (!newField.name.trim()) return;

    try {
      await axios.post(`${API_BASE}/config/classify_agent/custom_fields`, newField);

      setCustomFields([...customFields, newField]);
      setNewField({ name: '', type: 'text', required: false });
    } catch (error) {
      console.error('添加字段失败:', error);
    }
  };

  const removeCustomField = async (fieldName: string) => {
    try {
      await axios.delete(`${API_BASE}/config/classify_agent/custom_fields/${fieldName}`);
      setCustomFields(customFields.filter(f => f.name !== fieldName));
    } catch (error) {
      console.error('删除字段失败:', error);
    }
  };

  const addCategory = async (level: string, parentCode?: string) => {
    const categoryName = prompt('输入分类名称:');
    if (!categoryName) return;

    const categoryCode = prompt('输入分类代码 (如 AI_ML):');
    if (!categoryCode) return;

    try {
      await axios.post(`${API_BASE}/config/taxonomy/categories`, {
        level,
        parent_code: parentCode,
        label: categoryName,
        code: categoryCode,
        description: ''
      });

      loadConfig();
    } catch (error) {
      console.error('添加分类失败:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Taxonomy Configuration */}
      <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <span className="text-3xl">🏷️</span>
          分类层级配置
        </h2>

        <div className="space-y-4">
          {/* L1 Categories */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-white">一级分类 (L1)</h3>
              <button
                onClick={() => addCategory('L1')}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm transition-colors"
              >
                + 添加L1分类
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.entries(taxonomy).map(([key, category]) => (
                <div
                  key={key}
                  onClick={() => setSelectedL1(key)}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedL1 === key
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
                  }`}
                >
                  <div className="font-semibold">{category.code}</div>
                  <div className="text-sm opacity-75">{category.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* L2 Categories */}
          {selectedL1 && taxonomy[selectedL1]?.subcategories && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">
                  二级分类 (L2) - {taxonomy[selectedL1].label}
                </h3>
                <button
                  onClick={() => addCategory('L2', taxonomy[selectedL1].code)}
                  className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded-lg text-white text-sm transition-colors"
                >
                  + 添加L2分类
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {Object.entries(taxonomy[selectedL1].subcategories || {}).map(([key, subcat]) => (
                  <div
                    key={key}
                    className="p-3 bg-gray-700/50 rounded-lg"
                  >
                    <div className="font-semibold text-white">{subcat.code}</div>
                    <div className="text-sm text-gray-400">{subcat.label}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {Object.keys(subcat.subcategories || {}).length} L3分类
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Custom Fields Configuration */}
      <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <span className="text-3xl">📋</span>
          自定义字段配置
        </h2>

        {/* Existing Fields */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3">当前字段</h3>

          {customFields.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              暂无自定义字段，添加一个试试！
            </div>
          ) : (
            <div className="space-y-2">
              {customFields.map((field) => (
                <div
                  key={field.name}
                  className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="font-medium text-white">{field.name}</div>
                      <div className="text-sm text-gray-400">
                        类型: {field.type}
                        {field.required && (
                          <span className="ml-2 px-2 py-0.5 bg-red-500/20 text-red-300 rounded text-xs">
                            必填
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => removeCustomField(field.name)}
                    className="px-3 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-300 rounded-lg text-sm transition-colors"
                  >
                    删除
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add New Field */}
        <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-4 border border-blue-500/30">
          <h3 className="text-lg font-semibold text-white mb-3">添加新字段</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              type="text"
              value={newField.name}
              onChange={(e) => setNewField({ ...newField, name: e.target.value })}
              placeholder="字段名称..."
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            <select
              value={newField.type}
              onChange={(e) => setNewField({ ...newField, type: e.target.value })}
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="text">文本</option>
              <option value="number">数字</option>
              <option value="boolean">布尔值</option>
              <option value="select">下拉选择</option>
              <option value="multiselect">多选</option>
              <option value="date">日期</option>
            </select>

            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={newField.required}
                  onChange={(e) => setNewField({ ...newField, required: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm">必填</span>
              </label>

              <button
                onClick={addCustomField}
                disabled={!newField.name.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
              >
                添加字段
              </button>
            </div>
          </div>
        </div>

        {/* Field Examples */}
        <div className="mt-4 p-3 bg-gray-700/30 rounded-lg">
          <p className="text-sm text-gray-400 mb-2">💡 字段示例:</p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setNewField({ name: 'funding_amount', type: 'number', required: false })}
              className="px-3 py-1 bg-gray-600/50 hover:bg-gray-500/50 rounded text-xs text-gray-300 transition-colors"
            >
              融资金额
            </button>
            <button
              onClick={() => setNewField({ name: 'company_stage', type: 'select', required: false })}
              className="px-3 py-1 bg-gray-600/50 hover:bg-gray-500/50 rounded text-xs text-gray-300 transition-colors"
            >
              公司阶段
            </button>
            <button
              onClick={() => setNewField({ name: 'team_size', type: 'number', required: false })}
              className="px-3 py-1 bg-gray-600/50 hover:bg-gray-500/50 rounded text-xs text-gray-300 transition-colors"
            >
              团队规模
            </button>
            <button
              onClick={() => setNewField({ name: 'is_verified', type: 'boolean', required: false })}
              className="px-3 py-1 bg-gray-600/50 hover:bg-gray-500/50 rounded text-xs text-gray-300 transition-colors"
            >
              已验证
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
