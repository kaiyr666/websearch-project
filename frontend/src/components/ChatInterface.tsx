import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, FileUp, ExternalLink, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDropzone } from 'react-dropzone';

interface Message {
    id: string;
    role: 'user' | 'agent';
    content: string;
    type?: 'text' | 'upload_request' | 'jobs_table';
    data?: any;
}

interface Job {
    role: string;
    company: string;
    link: string;
    score: number;
    justification: string;
}

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [searchParams, setSearchParams] = useState<{ roles: string, country: string } | null>(null);
    const [searchHistory, setSearchHistory] = useState<any[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => { scrollToBottom(); }, [messages]);

    useEffect(() => {
        setMessages([{
            id: 'init',
            role: 'agent',
            content: "Hello, I'm Pathfinder—your intelligent job search assistant. What kind of role are you looking for?",
        }]);

        // Fetch search history
        axios.get('http://localhost:8000/search-history')
            .then(res => setSearchHistory(res.data.history || []))
            .catch(err => console.error('Failed to load history:', err));
    }, []);

    const handleSendMessage = async () => {
        if (!input.trim()) return;
        const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        const currentInput = input;
        setInput('');

        if (!searchParams) {
            setSearchParams({ roles: currentInput, country: 'Input' });
            setIsLoading(true);
            setTimeout(() => {
                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    role: 'agent',
                    content: "Excellent. To find the best matches for you, I'll need to review your resume. Please upload it below.",
                    type: 'upload_request'
                }]);
                setIsLoading(false);
            }, 600);
        }
    };

    const onDrop = async (acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        const uploadMsg: Message = { id: Date.now().toString(), role: 'user', content: `📄 ${file.name}` };
        setMessages(prev => [...prev, uploadMsg]);
        setIsLoading(true);

        try {
            const res = await axios.post('http://localhost:8000/parse-resume', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setMessages(prev => [...prev, {
                id: Date.now().toString() + '1',
                role: 'agent',
                content: "Perfect. I've analyzed your background and I'm now searching for positions that match your profile..."
            }]);

            performSearch(searchParams?.roles || "General", "USA", res.data.text);
        } catch (err) {
            setMessages(prev => [...prev, { id: 'err', role: 'agent', content: "I had trouble reading that file. Could you try uploading it again?" }]);
            setIsLoading(false);
        }
    };

    const performSearch = async (roles: string, country: string, resume: string) => {
        try {
            const res = await axios.post('http://localhost:8000/search-jobs', {
                roles: roles,
                country: country,
                resume_text: resume
            });

            if (!res.data.jobs || res.data.jobs.length === 0) {
                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    role: 'agent',
                    content: "I've searched through recent postings but couldn't find any strong matches at this time. Try broadening your search criteria or check back later."
                }]);
            } else {
                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    role: 'agent',
                    content: `I found ${res.data.jobs.length} excellent ${res.data.jobs.length === 1 ? 'match' : 'matches'} for you:`,
                    type: 'jobs_table',
                    data: res.data.jobs
                }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, { id: 'err', role: 'agent', content: "Something went wrong during the search. Please try again." }]);
        } finally {
            setIsLoading(false);
        }
    }

    const handleHistoryClick = async (id: number, query: string) => {
        if (isLoading) return;

        // Prevent duplicate loads of the same history item consecutively
        const lastMessage = messages[messages.length - 1];
        if (lastMessage?.data && lastMessage.data._historyId === id) {
            scrollToBottom();
            return;
        }

        setIsLoading(true);
        try {
            const res = await axios.get(`http://localhost:8000/search-results/${id}`);
            setMessages(prev => [...prev,
            { id: Date.now().toString(), role: 'user', content: `View history: ${query}` },
            {
                id: (Date.now() + 1).toString(),
                role: 'agent',
                content: `I found ${res.data.jobs.length} excellent matches from your previous search for "${query}":`,
                type: 'jobs_table',
                data: [...res.data.jobs].map(j => ({ ...j, _historyId: id })) // Tag with history ID
            }
            ]);
        } catch (err) {
            console.error('Failed to load search results:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'application/pdf': ['.pdf'] } });

    return (
        <div className="flex h-screen w-full bg-[hsl(var(--background))] text-[hsl(var(--foreground))] overflow-hidden">

            {/* Sidebar */}
            <aside className="w-64 bg-[#0F0E0D] border-r border-white/5 hidden lg:flex flex-col">
                <div className="p-6 border-b border-white/5">
                    <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-md bg-gradient-to-br from-[#D97757] via-[#E8956D] to-[#C26649] flex items-center justify-center shadow-lg shadow-[#D97757]/20">
                            <Sparkles size={16} className="text-white" />
                        </div>
                        <h1 className="font-serif text-xl font-semibold text-[#EBE5E0]">Pathfinder</h1>
                    </div>
                </div>

                <div className="flex-1 p-4">
                    <button
                        onClick={() => window.location.reload()}
                        className="w-full px-4 py-2.5 bg-[#D97757] hover:bg-[#C26649] text-white rounded-lg transition-all duration-200 font-medium text-sm shadow-md hover:shadow-lg hover:scale-[1.02]"
                    >
                        New Search
                    </button>

                    <div className="mt-8">
                        <h3 className="text-xs font-semibold text-zinc-600 uppercase tracking-wider mb-3 px-2">Recent</h3>
                        {searchHistory.length === 0 ? (
                            <div className="text-sm text-zinc-600 px-2 py-2">No searches yet</div>
                        ) : (
                            searchHistory.map((item: any) => (
                                <div
                                    key={item.id}
                                    className="text-sm text-zinc-400 px-2 py-2 hover:bg-white/5 rounded cursor-pointer transition-colors mb-1"
                                    title={`${item.job_count} matches found`}
                                    onClick={() => handleHistoryClick(item.id, item.query)}
                                >
                                    {item.query}
                                    <span className="text-xs text-zinc-600 ml-2">({item.job_count})</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col">

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto">
                    <div className="max-w-4xl mx-auto px-6 py-12 space-y-10">
                        {messages.map((msg) => (
                            <div key={msg.id} className="flex gap-6">
                                {/* Avatar - INLINE STYLES TEST */}
                                <div className="flex-shrink-0">
                                    <div
                                        className={cn("w-8 h-8 rounded-md flex items-center justify-center font-bold text-[11px] tracking-tight relative",
                                            msg.role === 'agent'
                                                ? "bg-gradient-to-br from-[#D97757] to-[#C26649] text-white"
                                                : "bg-zinc-700 text-zinc-300")}
                                        style={msg.role === 'agent' ? {
                                            boxShadow: '0 0 0 3px #D97757, 0 0 20px rgba(217, 119, 87, 0.6)',
                                            border: '2px solid #D97757'
                                        } : {}}>
                                        {msg.role === 'agent' ? 'AI' : 'YOU'}
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                    {msg.role === 'agent' && (
                                        <div className="font-serif text-sm mb-2 font-semibold" style={{ color: '#D97757' }}>Pathfinder</div>
                                    )}

                                    <div
                                        className={cn("text-[15px] leading-7 rounded-lg",
                                            msg.role === 'agent' ? "text-[#E5DED8] p-4" : "text-[#E5DED8]")}
                                        style={msg.role === 'agent' ? {
                                            background: 'linear-gradient(to right, rgba(217, 119, 87, 0.15), transparent)',
                                            borderLeft: '5px solid #D97757'
                                        } : {}}>
                                        {msg.content}
                                    </div>

                                    {/* Upload Widget */}
                                    {msg.type === 'upload_request' && (
                                        <div {...getRootProps()} className={cn(
                                            "mt-5 border-2 border-dashed rounded-xl p-8 cursor-pointer transition-all text-center",
                                            isDragActive
                                                ? "border-[#D97757] bg-[#D97757]/5"
                                                : "border-zinc-700 hover:border-zinc-600 hover:bg-white/[0.02]"
                                        )}>
                                            <input {...getInputProps()} />
                                            <FileUp className={cn(
                                                "w-8 h-8 mx-auto mb-3 transition-colors",
                                                isDragActive ? "text-[#D97757]" : "text-zinc-500"
                                            )} />
                                            <p className="font-medium text-zinc-300">Drop your resume here</p>
                                            <p className="text-sm text-zinc-500 mt-1">or click to browse (PDF only)</p>
                                        </div>
                                    )}

                                    {/* Jobs Table */}
                                    {msg.type === 'jobs_table' && msg.data && (
                                        <div className="mt-6 rounded-xl border border-white/5 overflow-hidden bg-[#1A1918]">
                                            <table className="w-full">
                                                <thead>
                                                    <tr className="border-b border-white/5 bg-white/[0.02]">
                                                        <th className="px-6 py-4 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                                                            Position
                                                        </th>
                                                        <th className="px-6 py-4 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                                                            Why it Matches
                                                        </th>
                                                        <th className="px-6 py-4 text-right text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                                                            Link
                                                        </th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-white/5">
                                                    {msg.data.map((job: Job, idx: number) => (
                                                        <tr key={idx} className="hover:bg-white/[0.02] transition-colors group">
                                                            <td className="px-6 py-5 align-top">
                                                                <div className="font-serif font-semibold text-[15px] text-[#E5DED8] mb-1">
                                                                    {job.role}
                                                                </div>
                                                                <div className="text-sm text-[#D97757]">
                                                                    {job.company}
                                                                </div>
                                                                {job.score >= 85 && (
                                                                    <div className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-semibold">
                                                                        ⭐ Top Match
                                                                    </div>
                                                                )}
                                                            </td>
                                                            <td className="px-6 py-5 text-sm text-zinc-400 leading-relaxed align-top max-w-md">
                                                                <span className="italic">"{job.justification}"</span>
                                                            </td>
                                                            <td className="px-6 py-5 text-right align-top">
                                                                <a
                                                                    href={job.link}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#D97757] hover:bg-[#C26649] text-white text-sm font-medium rounded-lg transition-colors shadow-sm opacity-0 group-hover:opacity-100"
                                                                >
                                                                    Apply <ExternalLink size={14} />
                                                                </a>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Loading State */}
                        {isLoading && (
                            <div className="flex gap-6">
                                <div className="w-8 h-8 rounded-md bg-[#D97757]/20 flex items-center justify-center shadow-lg shadow-[#D97757]/20">
                                    <div className="flex gap-1">
                                        <div className="w-1.5 h-1.5 bg-[#D97757] rounded-full animate-bounce [animation-delay:-0.3s]" />
                                        <div className="w-1.5 h-1.5 bg-[#D97757] rounded-full animate-bounce [animation-delay:-0.15s]" />
                                        <div className="w-1.5 h-1.5 bg-[#D97757] rounded-full animate-bounce" />
                                    </div>
                                </div>
                                <div className="text-sm text-zinc-500 self-center">Analyzing...</div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area - DRAMATIC STYLING */}
                <div className="border-t border-[#D97757]/20 p-6 pb-8 bg-gradient-to-t from-[#0D0C0B] via-[#1A1918] to-transparent">
                    <div className="max-w-4xl mx-auto">
                        <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                            className="relative">
                            <div className="flex items-end gap-3 bg-[#1F1E1D] border-2 border-[#D97757]/30 rounded-2xl p-3 focus-within:border-[#D97757] focus-within:ring-4 focus-within:ring-[#D97757]/20 transition-all">
                                <textarea
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            handleSendMessage();
                                        }
                                    }}
                                    placeholder="Describe the role you're looking for..."
                                    className="flex-1 bg-transparent border-none text-[15px] text-[#EBE5E0] placeholder:text-zinc-600 focus:ring-0 resize-none min-h-[44px] max-h-32 py-2 px-2"
                                    rows={1}
                                />
                                <button
                                    type="submit"
                                    disabled={!input.trim() || isLoading}
                                    className={cn(
                                        "p-3 rounded-lg transition-all duration-200",
                                        input.trim() && !isLoading
                                            ? "bg-gradient-to-r from-[#D97757] to-[#C26649] text-white scale-110 ring-2 ring-[#D97757]/50"
                                            : "bg-zinc-800 text-zinc-600 cursor-not-allowed"
                                    )}
                                >
                                    <Send size={16} className="font-bold" />
                                </button>
                            </div>
                        </form>
                        <p className="text-center mt-3 text-xs text-zinc-600">
                            Pathfinder can make mistakes. Verify important information.
                        </p>
                    </div>
                </div>

            </main>
        </div>
    );
}
