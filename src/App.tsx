/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';
import { Bot, Users, Hash, FileText, CheckCircle, Activity, Github } from 'lucide-react';
import { motion } from 'motion/react';

interface Stats {
  users: number;
  totalNumbers: number;
  availableNumbers: number;
  assignedNumbers: number;
  files: number;
}

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white font-sans overflow-hidden selection:bg-blue-500/30">
      {/* Background Glow */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 blur-[120px] rounded-full animate-pulse delay-700" />
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-16">
          <motion.div 
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="flex items-center gap-4"
          >
            <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center rotate-3 hover:rotate-0 transition-transform duration-300">
              <Bot size={36} className="text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
                DXA Number Bot
              </h1>
              <p className="text-white/40 font-mono text-sm mt-1 flex items-center gap-2">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                SYSTEM OPERATIONAL • V1.0.0
              </p>
            </div>
          </motion.div>

          <motion.div 
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="flex gap-4"
          >
            <a 
              href="https://t.me/dxa_universe" 
              target="_blank" 
              className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all duration-300 flex items-center gap-2 group"
            >
              <Github size={18} className="group-hover:rotate-12 transition-transform" />
              <span>DXA UNIVERSE</span>
            </a>
          </motion.div>
        </header>

        {/* Stats Grid */}
        <motion.div 
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          <StatCard 
            icon={<Users className="text-blue-400" />}
            label="Total Users"
            value={stats?.users || 0}
            subValue="Actively using bot"
            variant={item}
          />
          <StatCard 
            icon={<Hash className="text-purple-400" />}
            label="Total Numbers"
            value={stats?.totalNumbers || 0}
            subValue="Numbers in system"
            variant={item}
          />
          <StatCard 
            icon={<CheckCircle className="text-emerald-400" />}
            label="Available"
            value={stats?.availableNumbers || 0}
            subValue={`${Math.round((stats?.availableNumbers || 0) / (stats?.totalNumbers || 1) * 100)}% Stock`}
            variant={item}
          />
          <StatCard 
            icon={<FileText className="text-orange-400" />}
            label="Files Processed"
            value={stats?.files || 0}
            subValue="Number sets uploaded"
            variant={item}
          />
        </motion.div>

        {/* System Logs / Info */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-12 grid grid-cols-1 lg:grid-cols-3 gap-6"
        >
          <div className="lg:col-span-2 bg-white/[0.02] border border-white/5 rounded-3xl p-8 backdrop-blur-sm">
            <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Activity size={20} className="text-blue-500" />
              Live Bot Activity
            </h3>
            <div className="space-y-4">
              <LogItem time="JUST NOW" action="System Heartbeat" status="success" />
              <LogItem time="2 MIN AGO" action="Backup synchronization" status="success" />
              <LogItem time="5 MIN AGO" action="Stats refresh completed" status="success" />
              <LogItem time="12 MIN AGO" action="Database connection pool" status="success" />
            </div>
            
            <div className="mt-12 p-6 bg-blue-500/5 border border-blue-500/10 rounded-2xl">
              <h4 className="font-medium text-blue-400 mb-2">Bot Instructions</h4>
              <p className="text-white/60 text-sm leading-relaxed">
                Connect your Telegram client to <span className="text-blue-400">@dxa_number_bot</span> (or your configured bot). 
                Make sure you have joined the required channels to bypass the force-join check.
                Admin panel is restricted to ID <span className="text-white/80 font-mono">8197284774</span>.
              </p>
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-white/10 rounded-3xl p-8 flex flex-col justify-between">
            <div>
              <h3 className="text-2xl font-bold mb-4">Ready to Serve</h3>
              <p className="text-white/60 text-sm leading-relaxed mb-6">
                The bot is currently running in the background and listening for requests. 
                Any updates in the numbers database will reflect instantly here and in the bot commands.
              </p>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-white/40">API Status</span>
                <span className="text-emerald-400 font-mono">ONLINE</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/40">Latency</span>
                <span className="text-white/80 font-mono">24ms</span>
              </div>
              <button className="w-full py-4 bg-white text-black font-bold rounded-2xl hover:bg-white/90 transition-colors shadow-lg shadow-white/10">
                RESTART BOT
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, subValue, variant }: any) {
  return (
    <motion.div 
      variants={variant}
      className="bg-white/[0.02] border border-white/5 p-8 rounded-3xl hover:bg-white/[0.04] transition-colors group relative overflow-hidden"
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-[60px] translate-x-16 -translate-y-16 group-hover:bg-white/10 transition-colors" />
      <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <p className="text-white/40 text-sm font-medium mb-1 uppercase tracking-wider">{label}</p>
      <div className="flex items-baseline gap-2 mb-2">
        <h2 className="text-4xl font-bold tabular-nums">{value}</h2>
      </div>
      <p className="text-white/20 text-xs font-mono">{subValue}</p>
    </motion.div>
  );
}

function LogItem({ time, action, status }: any) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
      <div className="flex items-center gap-4">
        <span className="text-[10px] font-mono text-white/20 w-16">{time}</span>
        <span className="text-sm text-white/70">{action}</span>
      </div>
      <span className={`text-[10px] uppercase font-bold tracking-widest ${status === 'success' ? 'text-emerald-500' : 'text-red-500'}`}>
        • {status}
      </span>
    </div>
  );
}
