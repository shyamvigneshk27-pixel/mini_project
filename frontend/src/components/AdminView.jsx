import React from 'react';
import { motion } from 'framer-motion';
import { Users, Shield, Clock, ExternalLink } from 'lucide-react';

const AdminView = ({ sessions = [] }) => {
    // Filter to show only Admin logins as requested by user
    const adminSessions = sessions.filter(s => s.role === 'admin');

    // If no real sessions yet, show a placeholder but prefer real data
    const displaySessions = adminSessions.length > 0 ? adminSessions : [
        { id: 'ref', user: "System", role: "admin", loginTime: new Date().toLocaleString(), status: "Active", ip: "127.0.0.1" }
    ];

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-black text-white tracking-tighter">System Administration</h1>
                    <p className="text-gray-500 uppercase tracking-widest text-[10px] mt-1 font-bold">Privileged Access • Session Management</p>
                </div>
                <div className="flex gap-4">
                    <div className="glass-panel px-6 py-3 flex items-center gap-3 border-neon-blue/20">
                        <div className="w-2 h-2 bg-neon-blue rounded-full animate-pulse" />
                        <span className="text-xs font-bold text-white uppercase tracking-widest">System Online</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="glass-panel p-6 border-neon-purple/20">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 rounded-xl bg-neon-purple/10">
                            <Users className="w-6 h-6 text-neon-purple" />
                        </div>
                        <div>
                            <div className="text-2xl font-black text-white">12</div>
                            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">Total Staff</div>
                        </div>
                    </div>
                </div>
                <div className="glass-panel p-6 border-neon-blue/20">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 rounded-xl bg-neon-blue/10">
                            <Shield className="w-6 h-6 text-neon-blue" />
                        </div>
                        <div>
                            <div className="text-2xl font-black text-white">Active</div>
                            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">HIPAA Compliance</div>
                        </div>
                    </div>
                </div>
                <div className="glass-panel p-6 border-green-500/20">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="p-3 rounded-xl bg-green-500/10">
                            <Clock className="w-6 h-6 text-green-500" />
                        </div>
                        <div>
                            <div className="text-2xl font-black text-white">99.9%</div>
                            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">Uptime Score</div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="glass-panel overflow-hidden">
                <div className="px-8 py-6 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <Shield className="w-5 h-5 text-neon-purple" />
                        Secure User Sessions
                    </h3>
                    <button className="text-[10px] text-gray-500 hover:text-white uppercase font-black tracking-widest transition-colors flex items-center gap-2">
                        View Audit Log <ExternalLink className="w-3 h-3" />
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="text-left bg-black/20">
                                <th className="px-8 py-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">User Details</th>
                                <th className="px-8 py-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">Role</th>
                                <th className="px-8 py-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">Login Time</th>
                                <th className="px-8 py-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">IP Address</th>
                                <th className="px-8 py-4 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {displaySessions.map((session) => (
                                <tr key={session.id} className="hover:bg-white/[0.02] transition-colors group">
                                    <td className="px-8 py-6">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-xs font-bold text-gray-400 group-hover:text-neon-purple transition-colors">
                                                {session.user[0]}
                                            </div>
                                            <span className="font-bold text-gray-200">{session.user}</span>
                                        </div>
                                    </td>
                                    <td className="px-8 py-6">
                                        <span className={`text-[10px] px-2 py-1 rounded font-bold uppercase ${session.role === 'Admin' ? 'bg-neon-purple/10 text-neon-purple border border-neon-purple/20' : 'bg-gray-500/10 text-gray-400 border border-gray-500/20'
                                            }`}>
                                            {session.role}
                                        </span>
                                    </td>
                                    <td className="px-8 py-6 text-sm text-gray-500 font-medium font-mono">{session.loginTime}</td>
                                    <td className="px-8 py-6 text-sm text-gray-500 font-mono">{session.ip}</td>
                                    <td className="px-8 py-6 text-right">
                                        <span className={`inline-flex items-center gap-1.5 text-[10px] font-bold uppercase ${session.status === 'Active' ? 'text-green-500' : 'text-gray-600'
                                            }`}>
                                            <span className={`w-1.5 h-1.5 rounded-full ${session.status === 'Active' ? 'bg-green-500 animate-pulse' : 'bg-gray-600'}`} />
                                            {session.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AdminView;
