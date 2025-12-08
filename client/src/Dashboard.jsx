import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { X, TrendingUp, Target, Shield, Zap } from 'lucide-react';

const AnalyticsDashboard = ({ simulationId, onClose }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/simulation/${simulationId}/analytics`);
        const data = await response.json();
        setAnalytics(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [simulationId]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
        <div className="bg-gray-900 rounded-lg p-8 border border-gray-800">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  // Prepare data for charts
  const forceStrengthData = analytics.timestamps.map((time, idx) => ({
    time: time.toFixed(1),
    friendly: analytics.friendly_count[idx],
    enemy: analytics.enemy_count[idx]
  }));

  const roleData = analytics.timestamps.map((time, idx) => ({
    time: time.toFixed(1),
    hunter: analytics.role_distribution.hunter[idx],
    defender: analytics.role_distribution.defender[idx],
    interceptor: analytics.role_distribution.interceptor[idx]
  }));

  const finalRoleDistribution = [
    { name: 'Hunter', value: analytics.role_distribution.hunter[analytics.role_distribution.hunter.length - 1], color: '#ff6600' },
    { name: 'Defender', value: analytics.role_distribution.defender[analytics.role_distribution.defender.length - 1], color: '#00aaff' },
    { name: 'Interceptor', value: analytics.role_distribution.interceptor[analytics.role_distribution.interceptor.length - 1], color: '#ff0066' }
  ];

  const stats = analytics.statistics;

  return (
    <div className="fixed inset-0 bg-black/90 overflow-y-auto z-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600">
              Simulation Analytics
            </h2>
            <p className="text-gray-400 text-sm mt-1">Detailed Performance Analysis</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-cyan-900/50 to-cyan-800/30 rounded-lg p-4 border border-cyan-700/50">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-5 h-5 text-cyan-400" />
              <span className="text-sm text-gray-400">Survival Rate</span>
            </div>
            <div className="text-3xl font-bold text-cyan-400">
              {(stats.survival_rate * 100).toFixed(1)}%
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 rounded-lg p-4 border border-green-700/50">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-green-400" />
              <span className="text-sm text-gray-400">Kill Ratio</span>
            </div>
            <div className="text-3xl font-bold text-green-400">
              {stats.kill_ratio.toFixed(2)}:1
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 rounded-lg p-4 border border-blue-700/50">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              <span className="text-sm text-gray-400">Duration</span>
            </div>
            <div className="text-3xl font-bold text-blue-400">
              {stats.duration.toFixed(1)}s
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 rounded-lg p-4 border border-purple-700/50">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5 text-purple-400" />
              <span className="text-sm text-gray-400">Enemy Losses</span>
            </div>
            <div className="text-3xl font-bold text-purple-400">
              {stats.enemy_losses}
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Force Strength Over Time */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <h3 className="text-lg font-semibold mb-4">Force Strength Over Time</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={forceStrengthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="time" 
                  stroke="#888"
                  label={{ value: 'Time (s)', position: 'insideBottom', offset: -5, fill: '#888' }}
                />
                <YAxis 
                  stroke="#888"
                  label={{ value: 'Drone Count', angle: -90, position: 'insideLeft', fill: '#888' }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="friendly" 
                  stroke="#00aaff" 
                  strokeWidth={2}
                  dot={false}
                  name="Friendly Drones"
                />
                <Line 
                  type="monotone" 
                  dataKey="enemy" 
                  stroke="#ff3333" 
                  strokeWidth={2}
                  dot={false}
                  name="Enemy Drones"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Role Distribution Over Time */}
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <h3 className="text-lg font-semibold mb-4">Role Distribution Dynamics</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={roleData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="time" 
                  stroke="#888"
                  label={{ value: 'Time (s)', position: 'insideBottom', offset: -5, fill: '#888' }}
                />
                <YAxis 
                  stroke="#888"
                  label={{ value: 'Drone Count', angle: -90, position: 'insideLeft', fill: '#888' }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="hunter" 
                  stroke="#ff6600" 
                  strokeWidth={2}
                  dot={false}
                  name="Hunters"
                />
                <Line 
                  type="monotone" 
                  dataKey="defender" 
                  stroke="#00aaff" 
                  strokeWidth={2}
                  dot={false}
                  name="Defenders"
                />
                <Line 
                  type="monotone" 
                  dataKey="interceptor" 
                  stroke="#ff0066" 
                  strokeWidth={2}
                  dot={false}
                  name="Interceptors"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Final Role Distribution */}
        <div className="grid grid-cols-3 gap-6">
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <h3 className="text-lg font-semibold mb-4">Final Role Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={finalRoleDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {finalRoleDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Mission Summary */}
          <div className="col-span-2 bg-gray-900 rounded-lg p-4 border border-gray-800">
            <h3 className="text-lg font-semibold mb-4">Mission Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-800 rounded">
                <span className="text-gray-400">Friendly Losses</span>
                <span className="font-mono text-lg text-red-400">{stats.friendly_losses}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-800 rounded">
                <span className="text-gray-400">Enemy Destroyed</span>
                <span className="font-mono text-lg text-green-400">{stats.enemy_losses}</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-800 rounded">
                <span className="text-gray-400">Assets Protected</span>
                <span className="font-mono text-lg text-cyan-400">{stats.assets_protected}</span>
              </div>
              <div className={`mt-4 p-4 rounded-lg text-center text-lg font-semibold ${
                stats.mission_success 
                  ? 'bg-green-900/30 text-green-400 border border-green-700' 
                  : 'bg-red-900/30 text-red-400 border border-red-700'
              }`}>
                {stats.mission_success ? '✓ MISSION SUCCESS' : '✗ MISSION FAILED'}
              </div>
            </div>
          </div>
        </div>

        {/* Algorithm Performance Insights */}
        <div className="mt-6 bg-gradient-to-r from-cyan-900/20 to-blue-900/20 rounded-lg p-6 border border-cyan-800/50">
          <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            QIPFD Algorithm Performance Insights
          </h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-400 mb-1">Coordination Efficiency</p>
              <p className="text-cyan-400 font-semibold">
                {((1 - stats.friendly_losses / (stats.enemy_losses + 1)) * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-gray-400 mb-1">Adaptive Response</p>
              <p className="text-cyan-400 font-semibold">
                {analytics.role_distribution.hunter.length > 0 ? 'Excellent' : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 mb-1">Threat Neutralization Rate</p>
              <p className="text-cyan-400 font-semibold">
                {(stats.enemy_losses / Math.max(stats.duration, 1)).toFixed(2)} /sec
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;