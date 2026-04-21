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
  settings?: any;
}

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'settings'>('overview');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/stats');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          throw new TypeError("Oops, we haven't got JSON!");
        }
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
                {stats?.settings?.brand_name || 'DXA Number Bot'}
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
            <button 
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-3 rounded-xl transition-all duration-300 font-medium ${activeTab === 'overview' ? 'bg-blue-600' : 'bg-white/5 hover:bg-white/10 border border-white/10'}`}
            >
              Overview
            </button>
            <button 
              onClick={() => setActiveTab('settings')}
              className={`px-6 py-3 rounded-xl transition-all duration-300 font-medium ${activeTab === 'settings' ? 'bg-blue-600' : 'bg-white/5 hover:bg-white/10 border border-white/10'}`}
            >
              Settings
            </button>
          </motion.div>
        </header>

        {activeTab === 'overview' ? (
          <>
            {/* Stats Grid */}
            <motion.div 
              variants={container}
              initial="hidden"
              animate="show"
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              <StatCard 
                icon={<span className="text-2xl">🫂</span>}
                label="Total Users"
                value={stats?.users || 0}
                subValue="Actively using bot"
                variant={item}
                color="blue"
              />
              <StatCard 
                icon={<span className="text-2xl">🔢</span>}
                label="Total Numbers"
                value={stats?.totalNumbers || 0}
                subValue="Numbers in system"
                variant={item}
                color="purple"
              />
              <StatCard 
                icon={<span className="text-2xl">✅</span>}
                label="Available"
                value={stats?.availableNumbers || 0}
                subValue={`${Math.round((stats?.availableNumbers || 0) / (stats?.totalNumbers || 1) * 100)}% Stock`}
                variant={item}
                color="emerald"
              />
              <StatCard 
                icon={<span className="text-2xl">📁</span>}
                label="Files Processed"
                value={stats?.files || 0}
                subValue="Number sets uploaded"
                variant={item}
                color="orange"
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
                  <button 
                    onClick={() => {
                      setLoading(true);
                      setTimeout(() => window.location.reload(), 1000);
                    }}
                    className="w-full py-4 bg-white text-black font-bold rounded-2xl hover:bg-white/90 transition-colors shadow-lg shadow-white/10"
                  >
                    RESTART BOT
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        ) : (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-8"
          >
            <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 backdrop-blur-sm">
              <h3 className="text-2xl font-bold mb-8 flex items-center gap-2">
                <Bot size={24} className="text-blue-500" />
                Core Bot Configuration
              </h3>
              
              <div className="space-y-8">
                <div className="flex items-center justify-between p-6 bg-white/5 rounded-2xl border border-white/5">
                  <div>
                    <h4 className="font-semibold text-lg">Force Join System</h4>
                    <p className="text-white/40 text-sm">Enforce channel membership for all users</p>
                  </div>
                  <div className={`px-4 py-2 rounded-lg font-bold text-xs uppercase tracking-widest ${stats?.settings?.force_join ? "bg-emerald-500/20 text-emerald-500 border border-emerald-500/30" : "bg-red-500/20 text-red-500 border border-red-500/30"}`}>
                    {stats?.settings?.force_join ? "Active" : "Disabled"}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-lg mb-4">Required Channels</h4>
                  <div className="space-y-3">
                    {stats?.settings?.channels?.map((c: any, i: number) => (
                      <div key={i} className="p-4 bg-white/[0.03] border border-white/5 rounded-xl flex justify-between items-center">
                        <span className="font-medium">{c.name}</span>
                        <span className="text-white/30 font-mono text-xs">{c.username}</span>
                      </div>
                    ))}
                    {(stats?.settings?.channels?.length || 0) === 0 && (
                      <p className="text-white/20 italic">No channels configured</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-8">
              <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 backdrop-blur-sm">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <Users size={24} className="text-purple-500" />
                  Privileged Users
                </h3>
                <div className="space-y-2">
                  <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-xl flex justify-between items-center">
                    <span className="text-purple-400 font-bold">8197284774</span>
                    <span className="bg-purple-500/20 text-purple-400 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-widest">Master</span>
                  </div>
                  {stats?.settings?.admins?.map((a: any, i: number) => (
                    <div key={i} className="p-4 bg-white/[0.03] border border-white/5 rounded-xl flex justify-between items-center">
                      <span className="text-white/70">{a}</span>
                      <span className="text-white/20 text-[10px] font-bold uppercase tracking-widest italic">Co-Admin</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 backdrop-blur-sm">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <Activity size={24} className="text-blue-500" />
                  Appearance & Branding
                </h3>
                <div className="space-y-6">
                  <div>
                    <span className="text-white/40 text-xs font-mono block mb-2 uppercase tracking-widest">Brand Name</span>
                    <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl font-bold text-blue-400">
                      {stats?.settings?.brand_name || "DXA UNIVERSE"}
                    </div>
                  </div>
                  <div>
                    <span className="text-white/40 text-xs font-mono block mb-2 uppercase tracking-widest">Number Mask Text</span>
                    <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl font-mono text-sm text-blue-400">
                      {stats?.settings?.mask_text || "DXA"}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 backdrop-blur-sm">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <Bot size={24} className="text-emerald-500" />
                  OTP Group Buttons
                </h3>
                <div className="space-y-4">
                  {Object.entries(stats?.settings?.group_buttons || {}).map(([gid, btns]: [string, any], i) => (
                    <div key={i} className="space-y-2">
                      <span className="text-white/20 text-[10px] font-mono uppercase tracking-tighter">Group: {gid}</span>
                      <div className="flex flex-wrap gap-2">
                        {btns.map((b: any, j: number) => (
                          <div key={j} className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-400">
                            {b.text}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                  {Object.keys(stats?.settings?.group_buttons || {}).length === 0 && (
                    <p className="text-white/20 italic text-sm">No group-specific buttons</p>
                  )}
                </div>
              </div>

              <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 backdrop-blur-sm">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <FileText size={24} className="text-orange-500" />
                  Forwarding & Links
                </h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-white/40 text-xs font-mono block mb-2 uppercase tracking-widest">OTP Invitation Link</span>
                    <div className="p-4 bg-orange-500/5 border border-orange-500/20 rounded-xl break-all font-mono text-sm text-orange-400">
                      {stats?.settings?.otp_link || "https://t.me/dxaotpzone"}
                    </div>
                  </div>
                  <div>
                    <span className="text-white/40 text-xs font-mono block mb-2 uppercase tracking-widest">Forwarding Group IDs</span>
                    <div className="flex flex-wrap gap-2">
                      {stats?.settings?.otp_groups?.map((g: any, i: number) => (
                        <div key={i} className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-xs font-mono text-white/60">
                          {g}
                        </div>
                      ))}
                      {(stats?.settings?.otp_groups?.length || 0) === 0 && (
                        <span className="text-white/20 italic text-sm">None</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, subValue, variant, color }: any) {
  const colorMap: any = {
    blue: "from-blue-500/20 to-blue-600/5",
    purple: "from-purple-500/20 to-purple-600/5",
    emerald: "from-emerald-500/20 to-emerald-600/5",
    orange: "from-orange-500/20 to-orange-600/5"
  };

  return (
    <motion.div 
      variants={variant}
      className="bg-white/[0.02] border border-white/5 p-8 rounded-3xl hover:bg-white/[0.04] transition-all duration-500 group relative overflow-hidden"
    >
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${colorMap[color] || 'from-white/10 to-transparent'} rounded-full blur-[60px] translate-x-16 -translate-y-16 group-hover:scale-150 transition-transform duration-700`} />
      <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-white/10 group-hover:rotate-6 transition-all duration-300">
        <div className="group-hover:scale-125 transition-transform duration-300">
          {icon}
        </div>
      </div>
      <p className="text-white/40 text-sm font-medium mb-1 uppercase tracking-wider">{label}</p>
      <div className="flex items-baseline gap-2 mb-2">
        <h2 className="text-4xl font-black tracking-tighter tabular-nums text-white group-hover:text-blue-400 transition-colors">{value}</h2>
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
