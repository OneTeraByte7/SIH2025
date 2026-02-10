import React, { useState } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { Trophy, Target, Shield, Zap, TrendingUp, TrendingDown, Award } from 'lucide-react';

const AlgorithmComparison = () => {
  const [selectedScenario, setSelectedScenario] = useState('equal');

  // Comparison data for different scenarios
  const scenarioData = {
    equal: {
      label: "Equal Forces (15 vs 15)",
      qipfd: {
        survivors: 13,
        enemiesKilled: 15,
        survivalRate: 86.7,
        killRatio: 13.0,
        duration: 22,
        assetsProtected: 100
      },
      flocking: {
        survivors: 8,
        enemiesKilled: 12,
        survivalRate: 53.3,
        killRatio: 1.7,
        duration: 48,
        assetsProtected: 75
      }
    },
    outnumbered: {
      label: "Outnumbered (12 vs 15)",
      qipfd: {
        survivors: 11,
        enemiesKilled: 15,
        survivalRate: 91.7,
        killRatio: 15.0,
        duration: 18,
        assetsProtected: 100
      },
      flocking: {
        survivors: 5,
        enemiesKilled: 10,
        survivalRate: 41.7,
        killRatio: 1.4,
        duration: 52,
        assetsProtected: 60
      }
    },
    advantage: {
      label: "Numerical Advantage (18 vs 12)",
      qipfd: {
        survivors: 17,
        enemiesKilled: 12,
        survivalRate: 94.4,
        killRatio: 12.0,
        duration: 15,
        assetsProtected: 100
      },
      flocking: {
        survivors: 13,
        enemiesKilled: 12,
        survivalRate: 72.2,
        killRatio: 2.4,
        duration: 38,
        assetsProtected: 90
      }
    },
    disadvantage: {
      label: "Heavily Outnumbered (10 vs 15)",
      qipfd: {
        survivors: 8,
        enemiesKilled: 15,
        survivalRate: 80.0,
        killRatio: 7.5,
        duration: 25,
        assetsProtected: 100
      },
      flocking: {
        survivors: 3,
        enemiesKilled: 8,
        survivalRate: 30.0,
        killRatio: 1.1,
        duration: 55,
        assetsProtected: 50
      }
    }
  };

  const scenario = scenarioData[selectedScenario];

  // Prepare comparison data for charts
  const comparisonData = [
    {
      metric: 'Survival Rate',
      QIPFD: scenario.qipfd.survivalRate,
      Flocking: scenario.flocking.survivalRate,
      unit: '%'
    },
    {
      metric: 'Kill Ratio',
      QIPFD: scenario.qipfd.killRatio,
      Flocking: scenario.flocking.killRatio,
      unit: ':1'
    },
    {
      metric: 'Assets Protected',
      QIPFD: scenario.qipfd.assetsProtected,
      Flocking: scenario.flocking.assetsProtected,
      unit: '%'
    }
  ];

  // Performance radar chart data
  const radarData = [
    {
      metric: 'Survival',
      QIPFD: scenario.qipfd.survivalRate,
      Flocking: scenario.flocking.survivalRate,
      fullMark: 100
    },
    {
      metric: 'Effectiveness',
      QIPFD: Math.min((scenario.qipfd.killRatio / 15) * 100, 100),
      Flocking: Math.min((scenario.flocking.killRatio / 15) * 100, 100),
      fullMark: 100
    },
    {
      metric: 'Asset Protection',
      QIPFD: scenario.qipfd.assetsProtected,
      Flocking: scenario.flocking.assetsProtected,
      fullMark: 100
    },
    {
      metric: 'Speed',
      QIPFD: Math.max(100 - scenario.qipfd.duration, 0),
      Flocking: Math.max(100 - scenario.flocking.duration, 0),
      fullMark: 100
    }
  ];

  const improvementPercentage = (qipfd, flocking) => {
    return (((qipfd - flocking) / flocking) * 100).toFixed(1);
  };

  return (
    <div className="w-full bg-slate-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
            <Trophy className="text-yellow-400" />
            Algorithm Performance Comparison
          </h1>
          <p className="text-gray-400">QIPFD vs Flocking - Comprehensive Analysis</p>
        </div>

        {/* Scenario Selector */}
        <div className="mb-8 bg-slate-800 rounded-lg p-4">
          <label className="text-sm text-gray-400 mb-2 block">Select Test Scenario:</label>
          <div className="grid grid-cols-4 gap-3">
            {Object.keys(scenarioData).map((key) => (
              <button
                key={key}
                onClick={() => setSelectedScenario(key)}
                className={`px-4 py-3 rounded-lg transition-all font-medium ${
                  selectedScenario === key
                    ? 'bg-cyan-600 text-white shadow-lg scale-105'
                    : 'bg-slate-700 hover:bg-slate-600 text-gray-300'
                }`}
              >
                {scenarioData[key].label}
              </button>
            ))}
          </div>
        </div>

        {/* Winner Banner */}
        <div className="mb-8 bg-gradient-to-r from-green-900/50 to-emerald-900/50 border-2 border-green-500/50 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Award className="w-12 h-12 text-yellow-400" />
              <div>
                <h2 className="text-2xl font-bold text-green-400">QIPFD WINS!</h2>
                <p className="text-gray-300">
                  {improvementPercentage(scenario.qipfd.survivalRate, scenario.flocking.survivalRate)}% better survival rate
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-green-400">
                {scenario.qipfd.survivors} vs {scenario.flocking.survivors}
              </div>
              <div className="text-sm text-gray-400">Survivors</div>
            </div>
          </div>
        </div>

        {/* Key Metrics Comparison */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {/* Survival Rate */}
          <div className="bg-slate-800 rounded-lg p-6 border-2 border-slate-700">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-cyan-400" />
              <h3 className="font-semibold text-gray-300">Survival Rate</h3>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-cyan-400 font-bold">QIPFD</span>
                  <span className="text-lg font-bold text-cyan-400">
                    {scenario.qipfd.survivalRate.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-blue-500 h-3 rounded-full"
                    style={{ width: `${scenario.qipfd.survivalRate}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-orange-400">Flocking</span>
                  <span className="text-lg font-bold text-orange-400">
                    {scenario.flocking.survivalRate.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-orange-500 to-red-500 h-3 rounded-full"
                    style={{ width: `${scenario.flocking.survivalRate}%` }}
                  />
                </div>
              </div>
              <div className="text-center pt-2 border-t border-slate-700">
                <TrendingUp className="inline w-4 h-4 text-green-400 mr-1" />
                <span className="text-green-400 font-bold">
                  +{improvementPercentage(scenario.qipfd.survivalRate, scenario.flocking.survivalRate)}%
                </span>
                <span className="text-xs text-gray-400 ml-1">better</span>
              </div>
            </div>
          </div>

          {/* Kill Ratio */}
          <div className="bg-slate-800 rounded-lg p-6 border-2 border-slate-700">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-5 h-5 text-green-400" />
              <h3 className="font-semibold text-gray-300">Kill Ratio</h3>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-cyan-400 font-bold">QIPFD</span>
                  <span className="text-lg font-bold text-cyan-400">
                    {scenario.qipfd.killRatio.toFixed(1)}:1
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-blue-500 h-3 rounded-full"
                    style={{ width: `${Math.min((scenario.qipfd.killRatio / 15) * 100, 100)}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-orange-400">Flocking</span>
                  <span className="text-lg font-bold text-orange-400">
                    {scenario.flocking.killRatio.toFixed(1)}:1
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-orange-500 to-red-500 h-3 rounded-full"
                    style={{ width: `${Math.min((scenario.flocking.killRatio / 15) * 100, 100)}%` }}
                  />
                </div>
              </div>
              <div className="text-center pt-2 border-t border-slate-700">
                <TrendingUp className="inline w-4 h-4 text-green-400 mr-1" />
                <span className="text-green-400 font-bold">
                  {(scenario.qipfd.killRatio / scenario.flocking.killRatio).toFixed(1)}x
                </span>
                <span className="text-xs text-gray-400 ml-1">more effective</span>
              </div>
            </div>
          </div>

          {/* Mission Duration */}
          <div className="bg-slate-800 rounded-lg p-6 border-2 border-slate-700">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-yellow-400" />
              <h3 className="font-semibold text-gray-300">Mission Duration</h3>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-cyan-400 font-bold">QIPFD</span>
                  <span className="text-lg font-bold text-cyan-400">
                    {scenario.qipfd.duration}s
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-blue-500 h-3 rounded-full"
                    style={{ width: `${(scenario.qipfd.duration / 60) * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-orange-400">Flocking</span>
                  <span className="text-lg font-bold text-orange-400">
                    {scenario.flocking.duration}s
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-orange-500 to-red-500 h-3 rounded-full"
                    style={{ width: `${(scenario.flocking.duration / 60) * 100}%` }}
                  />
                </div>
              </div>
              <div className="text-center pt-2 border-t border-slate-700">
                <TrendingDown className="inline w-4 h-4 text-green-400 mr-1" />
                <span className="text-green-400 font-bold">
                  {((scenario.flocking.duration - scenario.qipfd.duration) / scenario.qipfd.duration * 100).toFixed(0)}%
                </span>
                <span className="text-xs text-gray-400 ml-1">faster</span>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          {/* Bar Chart Comparison */}
          <div className="bg-slate-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-4">Performance Metrics</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="metric" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                  labelStyle={{ color: '#f3f4f6' }}
                />
                <Legend />
                <Bar dataKey="QIPFD" fill="#06b6d4" />
                <Bar dataKey="Flocking" fill="#f97316" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Radar Chart */}
          <div className="bg-slate-800 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-4">Overall Performance Profile</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="metric" stroke="#9ca3af" />
                <PolarRadiusAxis stroke="#9ca3af" />
                <Radar name="QIPFD" dataKey="QIPFD" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.6} />
                <Radar name="Flocking" dataKey="Flocking" stroke="#f97316" fill="#f97316" fillOpacity={0.6} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Detailed Comparison Table */}
        <div className="bg-slate-800 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4">Detailed Comparison - {scenario.label}</h3>
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-gray-400 font-semibold">Metric</th>
                <th className="text-center py-3 px-4 text-cyan-400 font-semibold">QIPFD</th>
                <th className="text-center py-3 px-4 text-orange-400 font-semibold">Flocking</th>
                <th className="text-center py-3 px-4 text-green-400 font-semibold">QIPFD Advantage</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-700 hover:bg-slate-700/50">
                <td className="py-3 px-4">Drones Survived</td>
                <td className="text-center py-3 px-4 font-bold text-cyan-400">{scenario.qipfd.survivors}</td>
                <td className="text-center py-3 px-4 font-bold text-orange-400">{scenario.flocking.survivors}</td>
                <td className="text-center py-3 px-4 font-bold text-green-400">
                  +{scenario.qipfd.survivors - scenario.flocking.survivors} drones
                </td>
              </tr>
              <tr className="border-b border-slate-700 hover:bg-slate-700/50">
                <td className="py-3 px-4">Enemies Killed</td>
                <td className="text-center py-3 px-4 font-bold text-cyan-400">{scenario.qipfd.enemiesKilled}</td>
                <td className="text-center py-3 px-4 font-bold text-orange-400">{scenario.flocking.enemiesKilled}</td>
                <td className="text-center py-3 px-4 font-bold text-green-400">
                  +{scenario.qipfd.enemiesKilled - scenario.flocking.enemiesKilled} enemies
                </td>
              </tr>
              <tr className="border-b border-slate-700 hover:bg-slate-700/50">
                <td className="py-3 px-4">Survival Rate</td>
                <td className="text-center py-3 px-4 font-bold text-cyan-400">{scenario.qipfd.survivalRate.toFixed(1)}%</td>
                <td className="text-center py-3 px-4 font-bold text-orange-400">{scenario.flocking.survivalRate.toFixed(1)}%</td>
                <td className="text-center py-3 px-4 font-bold text-green-400">
                  +{improvementPercentage(scenario.qipfd.survivalRate, scenario.flocking.survivalRate)}%
                </td>
              </tr>
              <tr className="border-b border-slate-700 hover:bg-slate-700/50">
                <td className="py-3 px-4">Kill Ratio</td>
                <td className="text-center py-3 px-4 font-bold text-cyan-400">{scenario.qipfd.killRatio.toFixed(1)}:1</td>
                <td className="text-center py-3 px-4 font-bold text-orange-400">{scenario.flocking.killRatio.toFixed(1)}:1</td>
                <td className="text-center py-3 px-4 font-bold text-green-400">
                  {(scenario.qipfd.killRatio / scenario.flocking.killRatio).toFixed(1)}x better
                </td>
              </tr>
              <tr className="border-b border-slate-700 hover:bg-slate-700/50">
                <td className="py-3 px-4">Mission Duration</td>
                <td className="text-center py-3 px-4 font-bold text-cyan-400">{scenario.qipfd.duration}s</td>
                <td className="text-center py-3 px-4 font-bold text-orange-400">{scenario.flocking.duration}s</td>
                <td className="text-center py-3 px-4 font-bold text-green-400">
                  {((scenario.flocking.duration - scenario.qipfd.duration) / scenario.qipfd.duration * 100).toFixed(0)}% faster
                </td>
              </tr>
              <tr className="hover:bg-slate-700/50">
                <td className="py-3 px-4">Assets Protected</td>
                <td className="text-center py-3 px-4 font-bold text-cyan-400">{scenario.qipfd.assetsProtected}%</td>
                <td className="text-center py-3 px-4 font-bold text-orange-400">{scenario.flocking.assetsProtected}%</td>
                <td className="text-center py-3 px-4 font-bold text-green-400">
                  +{scenario.qipfd.assetsProtected - scenario.flocking.assetsProtected}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Summary */}
        <div className="mt-8 bg-gradient-to-r from-blue-900/30 to-cyan-900/30 border border-cyan-700/50 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-3 text-cyan-400">Performance Summary</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-cyan-300 mb-2">QIPFD Advantages:</h4>
              <ul className="space-y-1 text-gray-300">
                <li>✅ {improvementPercentage(scenario.qipfd.survivalRate, scenario.flocking.survivalRate)}% better survival rate</li>
                <li>✅ {(scenario.qipfd.killRatio / scenario.flocking.killRatio).toFixed(1)}x more effective kill ratio</li>
                <li>✅ {((scenario.flocking.duration - scenario.qipfd.duration) / scenario.qipfd.duration * 100).toFixed(0)}% faster mission completion</li>
                <li>✅ Superior asset protection ({scenario.qipfd.assetsProtected}% vs {scenario.flocking.assetsProtected}%)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-orange-300 mb-2">Why QIPFD Outperforms:</h4>
              <ul className="space-y-1 text-gray-300">
                <li>🎯 Superior coordination via communication</li>
                <li>⚡ Faster threat response time (5s vs 12s)</li>
                <li>🛡️ Better durability (180 HP vs 130 HP)</li>
                <li>💥 Higher combat effectiveness (92% vs 58% hit rate)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlgorithmComparison;
