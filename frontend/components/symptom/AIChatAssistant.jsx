// "use client";

// import { useState, useRef, useEffect, memo } from "react";
// import { userApi } from "@/lib/api-services";
// import { Input } from "@/components/ui/input";
// import { Button } from "@/components/ui/button";
// import { ScrollArea } from "@/components/ui/scroll-area";
// import { 
//   Send, 
//   Copy, 
//   ChevronDown, 
//   ChevronUp, 
//   Bot, 
//   User, 
//   Sparkles, 
//   Terminal,
//   Check
// } from "lucide-react";
// import { toast } from "sonner";

// // Markdown Imports
// import ReactMarkdown from "react-markdown";
// import remarkGfm from "remark-gfm";
// import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
// import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

// /* --- Utility: Robust JSON Detection --- */
// const isJsonString = (str) => {
//   if (typeof str !== "string") return false;
//   const cleaned = str.trim();
//   if (!cleaned.startsWith("{") && !cleaned.startsWith("[")) return false;
//   try {
//     JSON.parse(cleaned);
//     return true;
//   } catch (e) {
//     return false;
//   }
// };

// /* --- Sub-Component: Loading Indicator --- */
// const LoadingBubbles = () => (
//   <div className="flex space-x-1 items-center p-2 h-6">
//     <div className="w-2 h-2 bg-black rounded-full animate-bounce [animation-delay:-0.3s]"></div>
//     <div className="w-2 h-2 bg-black rounded-full animate-bounce [animation-delay:-0.15s]"></div>
//     <div className="w-2 h-2 bg-black rounded-full animate-bounce"></div>
//   </div>
// );

// /* --- Sub-Component: Copy Button for Code Blocks --- */
// const CodeCopyBtn = ({ text }) => {
//   const [copied, setCopied] = useState(false);

//   const onCopy = () => {
//     navigator.clipboard.writeText(text);
//     setCopied(true);
//     setTimeout(() => setCopied(false), 2000);
//   };

//   return (
//     <button 
//       onClick={onCopy} 
//       className="absolute right-2 top-2 text-xs text-gray-400 hover:text-white flex items-center gap-1"
//     >
//       {copied ? <Check size={14} /> : <Copy size={14} />}
//       {copied ? "Copied" : "Copy"}
//     </button>
//   );
// };

// /* --- Sub-Component: Styled JSON Block --- */
// function JsonBlock({ text }) {
//   const [open, setOpen] = useState(true);
//   const parsed = JSON.parse(text);

//   const copyToClipboard = () => {
//     navigator.clipboard.writeText(text);
//     toast.success("JSON copied");
//   };

//   return (
//     <div className="w-full my-3 border-2 border-black rounded-md overflow-hidden shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] bg-white">
//       <div className="flex justify-between items-center bg-neutral-100 border-b-2 border-black p-2 select-none cursor-pointer" onClick={() => setOpen(!open)}>
//         <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
//           <Terminal size={14} />
//           JSON Output
//         </div>
//         <div className="flex gap-1">
//           <Button
//             size="icon"
//             variant="ghost"
//             className="h-6 w-6 hover:bg-black hover:text-white rounded-sm"
//             onClick={(e) => { e.stopPropagation(); copyToClipboard(); }}
//           >
//             <Copy size={12} />
//           </Button>
//           <div className="h-6 w-6 flex items-center justify-center">
//              {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
//           </div>
//         </div>
//       </div>
      
//       {open && (
//         <div className="bg-white p-3 overflow-x-auto max-h-[300px]">
//           <pre className="text-xs font-mono text-neutral-800 leading-relaxed">
//             {JSON.stringify(parsed, null, 2)}
//           </pre>
//         </div>
//       )}
//     </div>
//   );
// }

// /* --- Memoized Markdown Component --- */
// // We memoize this so it doesn't re-render heavily while typing
// const MarkdownContent = memo(({ content }) => {
//   return (
//     <ReactMarkdown
//       remarkPlugins={[remarkGfm]}
//       components={{
//         // Custom styling for standard HTML elements to match Brutalist theme
//         p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
//         ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
//         ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
//         li: ({ children }) => <li className="pl-1">{children}</li>,
//         h1: ({ children }) => <h1 className="text-xl font-black mb-2 mt-4 uppercase">{children}</h1>,
//         h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3 border-b-2 border-black inline-block">{children}</h2>,
//         h3: ({ children }) => <h3 className="text-base font-bold mb-1 mt-2">{children}</h3>,
//         blockquote: ({ children }) => (
//           <blockquote className="border-l-4 border-black pl-4 italic my-2 bg-gray-100 py-1 pr-2 rounded-r">
//             {children}
//           </blockquote>
//         ),
//         a: ({ href, children }) => (
//           <a href={href} target="_blank" rel="noopener noreferrer" className="underline font-bold decoration-2 decoration-black hover:bg-black hover:text-white transition-colors">
//             {children}
//           </a>
//         ),
//         table: ({ children }) => (
//           <div className="overflow-x-auto my-3 border-2 border-black rounded-lg">
//             <table className="min-w-full text-sm text-left">{children}</table>
//           </div>
//         ),
//         thead: ({ children }) => <thead className="bg-black text-white uppercase font-bold">{children}</thead>,
//         th: ({ children }) => <th className="px-4 py-2 border-r border-white last:border-r-0">{children}</th>,
//         td: ({ children }) => <td className="px-4 py-2 border-b border-gray-200 border-r border-black last:border-r-0">{children}</td>,
        
//         // Code blocks vs Inline code
//         code({ node, inline, className, children, ...props }) {
//           const match = /language-(\w+)/.exec(className || "");
//           return !inline && match ? (
//             <div className="relative group my-3 rounded-lg overflow-hidden border-2 border-black shadow-sm">
//               <div className="bg-[#1e1e1e] px-3 py-1 text-xs text-gray-400 flex justify-between items-center border-b border-gray-700">
//                  <span>{match[1]}</span>
//                  <CodeCopyBtn text={String(children).replace(/\n$/, "")} />
//               </div>
//               <SyntaxHighlighter
//                 {...props}
//                 style={vscDarkPlus}
//                 language={match[1]}
//                 PreTag="div"
//                 customStyle={{ margin: 0, borderRadius: 0 }}
//               >
//                 {String(children).replace(/\n$/, "")}
//               </SyntaxHighlighter>
//             </div>
//           ) : (
//             <code {...props} className="bg-neutral-200 text-red-600 px-1 py-0.5 rounded font-mono text-sm border border-neutral-300">
//               {children}
//             </code>
//           );
//         },
//       }}
//     >
//       {content}
//     </ReactMarkdown>
//   );
// });
// MarkdownContent.displayName = "MarkdownContent";


// /* --- Main Component --- */
// export default function GeminiChat() {
//   const [messages, setMessages] = useState([]);
//   const [input, setInput] = useState("");
//   const [isLoading, setIsLoading] = useState(false);
//   const scrollRef = useRef(null);

//   /* Auto-scroll */
//   useEffect(() => {
//     scrollRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [messages, isLoading]);

//   const sendMessage = async () => {
//     if (!input.trim() || isLoading) return;

//     const userMsg = { role: "user", content: input };
//     setMessages((prev) => [...prev, userMsg]);
//     setInput("");
//     setIsLoading(true);

//     try {
//       const res = await userApi.geminiChat(userMsg.content);
      
//       // Handle various response formats
//       let botContent = "";
//       if (typeof res === "string") {
//         botContent = res;
//       } else if (res.assistant) {
//         botContent = res.assistant;
//       } else if (res.message) {
//         botContent = res.message;
//       } else {
//         botContent = JSON.stringify(res);
//       }
      
//       setMessages((prev) => [...prev, { role: "assistant", content: botContent }]);
//     } catch (error) {
//       toast.error("Failed to connect");
//       setMessages((prev) => [
//         ...prev,
//         { role: "assistant", content: "**Error**: Could not fetch response from Gemini." },
//       ]);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <div className="flex flex-col h-[85vh] max-w-4xl mx-auto p-4">
      
//       {/* Header */}
//       <header className="flex items-center justify-between mb-6 border-b-2 border-black pb-4">
//         <div className="flex items-center gap-3">
//           <div className="p-2 bg-black text-white rounded-lg shadow-[3px_3px_0px_0px_rgba(0,0,0,0.3)]">
//             <Sparkles size={20} />
//           </div>
//           <div>
//             <h1 className="text-xl font-black uppercase tracking-tight">AI Assistant Chat</h1>
//             <p className="text-xs font-medium text-neutral-500">Markdown Enabled • v2.1</p>
//           </div>
//         </div>
//         <div className={`text-xs font-mono border border-black px-2 py-1 rounded transition-colors ${isLoading ? "bg-yellow-300" : "bg-neutral-50"}`}>
//           {isLoading ? "STATUS: PROCESSING" : "STATUS: IDLE"}
//         </div>
//       </header>

//       {/* Chat Area */}
//       <div className="flex-1 relative bg-neutral-50 border-2 border-black rounded-xl overflow-hidden shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
//         <ScrollArea className="h-full p-4 sm:p-6">
//           <div className="flex flex-col space-y-6 pb-4">
            
//             {messages.length === 0 && (
//               <div className="text-center mt-20 opacity-40">
//                 <Bot size={48} className="mx-auto mb-2" />
//                 <p className="font-mono text-sm">Start a conversation...</p>
//               </div>
//             )}

//             {messages.map((msg, i) => {
//               const isUser = msg.role === "user";
//               const isJson = !isUser && isJsonString(msg.content);

//               return (
//                 <div
//                   key={i}
//                   className={`flex gap-3 w-full ${isUser ? "justify-end" : "justify-start"}`}
//                 >
//                   {!isUser && (
//                     <div className="flex-shrink-0 w-8 h-8 bg-white border-2 border-black rounded-full flex items-center justify-center mt-1">
//                       <Bot size={16} />
//                     </div>
//                   )}

//                   <div
//                     className={`relative max-w-[85%] sm:max-w-[80%] p-4 rounded-xl text-sm ${
//                       isUser
//                         ? "bg-black text-white rounded-tr-none shadow-[4px_4px_0px_0px_rgba(100,100,100,0.5)]"
//                         : "bg-white text-black border-2 border-black rounded-tl-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
//                     }`}
//                   >
//                     {isJson ? (
//                       <JsonBlock text={msg.content} />
//                     ) : (
//                       // Use the Markdown Component for bot, regular text for user
//                       isUser ? (
//                         <div className="whitespace-pre-wrap font-medium">{msg.content}</div>
//                       ) : (
//                         <MarkdownContent content={msg.content} />
//                       )
//                     )}
//                   </div>

//                   {isUser && (
//                     <div className="flex-shrink-0 w-8 h-8 bg-black text-white rounded-full flex items-center justify-center mt-1">
//                       <User size={16} />
//                     </div>
//                   )}
//                 </div>
//               );
//             })}

//             {isLoading && (
//               <div className="flex gap-3 w-full justify-start animate-pulse">
//                  <div className="flex-shrink-0 w-8 h-8 bg-white border-2 border-black rounded-full flex items-center justify-center">
//                     <Bot size={16} />
//                   </div>
//                   <div className="bg-white border-2 border-black rounded-xl rounded-tl-none p-3 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
//                     <LoadingBubbles />
//                   </div>
//               </div>
//             )}
            
//             <div ref={scrollRef} />
//           </div>
//         </ScrollArea>
//       </div>

//       {/* Input Footer */}
//       <div className="mt-6">
//         <div className="flex items-center gap-2 bg-white border-2 border-black p-2 rounded-xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus-within:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] focus-within:translate-x-[2px] focus-within:translate-y-[2px] transition-all">
//           <Input
//             className="flex-1 border-none focus-visible:ring-0 shadow-none bg-transparent text-base placeholder:text-neutral-400 font-medium"
//             placeholder="Ask something..."
//             value={input}
//             onChange={(e) => setInput(e.target.value)}
//             onKeyDown={(e) => e.key === "Enter" && !isLoading && sendMessage()}
//             disabled={isLoading}
//             autoFocus
//           />
//           <Button
//             onClick={sendMessage}
//             disabled={isLoading || !input.trim()}
//             className={`
//               h-10 px-4 rounded-lg border-2 border-black font-bold transition-all
//               ${
//                 !input.trim() || isLoading 
//                 ? "bg-neutral-200 text-neutral-400 border-neutral-300 cursor-not-allowed" 
//                 : "bg-black text-white hover:bg-white hover:text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,0.5)] hover:translate-y-[1px] hover:translate-x-[1px] hover:shadow-none"
//               }
//             `}
//           >
//             {isLoading ? (
//                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
//             ) : (
//               <div className="flex items-center gap-2">
//                 <span>SEND</span>
//                 <Send size={16} />
//               </div>
//             )}
//           </Button>
//         </div>
//       </div>
//     </div>
//   );
// }

"use client";

import { useState, useRef, useEffect, memo } from "react";
import { userApi } from "@/lib/api-services";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  ArrowUp, 
  Copy, 
  ChevronDown, 
  ChevronUp, 
  Check,
  Cpu,
  Circle
} from "lucide-react";
import { toast } from "sonner";

// Markdown Imports
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism"; 
import { Card } from "../ui/card";

/* --- Utility: JSON Check --- */
const isJsonString = (str) => {
  if (typeof str !== "string") return false;
  const cleaned = str.trim();
  if (!cleaned.startsWith("{") && !cleaned.startsWith("[")) return false;
  try {
    JSON.parse(cleaned);
    return true;
  } catch (e) {
    return false;
  }
};

/* --- Sub-Component: Minimal Loader --- */
const LoadingDots = () => (
  <div className="flex space-x-1 items-center h-6">
    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"></div>
    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse delay-75"></div>
    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse delay-150"></div>
  </div>
);

/* --- Sub-Component: Minimal Copy Button --- */
const CodeCopyBtn = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const onCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={onCopy} className="text-gray-400 hover:text-black transition-colors">
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );
};

/* --- Sub-Component: Minimal JSON Block --- */
function JsonBlock({ text }) {
  const [open, setOpen] = useState(true);
  const parsed = JSON.parse(text);

  return (
    <div className="w-full my-3 border border-gray-200 rounded-lg bg-gray-50/50">
      <div 
        className="flex justify-between items-center px-3 py-2 cursor-pointer select-none border-b border-gray-100"
        onClick={() => setOpen(!open)}
      >
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">JSON Data</span>
        <div className="flex items-center gap-2">
          <Button size="icon" variant="ghost" className="h-5 w-5 text-gray-400" onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(text); toast.success("Copied"); }}>
            <Copy size={12} />
          </Button>
          <div className="text-gray-400">
            {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </div>
        </div>
      </div>
      {open && (
        <div className="p-3 overflow-x-auto">
          <pre className="text-xs font-mono text-gray-600">
            {JSON.stringify(parsed, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

/* --- Memoized Markdown (Swiss Styled) --- */
const MarkdownContent = memo(({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-3 last:mb-0 text-gray-800 leading-7">{children}</p>,
        ul: ({ children }) => <ul className="list-disc pl-4 mb-3 space-y-1 text-gray-800 marker:text-gray-400">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-4 mb-3 space-y-1 text-gray-800 marker:text-gray-400">{children}</ol>,
        h1: ({ children }) => <h1 className="text-lg font-semibold text-gray-900 mb-3 mt-6 tracking-tight">{children}</h1>,
        h2: ({ children }) => <h2 className="text-base font-semibold text-gray-900 mb-2 mt-4 tracking-tight">{children}</h2>,
        blockquote: ({ children }) => <blockquote className="border-l-2 border-gray-200 pl-4 italic text-gray-500 my-3">{children}</blockquote>,
        a: ({ href, children }) => <a href={href} target="_blank" rel="noopener" className="text-black font-medium underline decoration-gray-300 hover:decoration-black underline-offset-2 transition-all">{children}</a>,
        table: ({ children }) => <div className="overflow-x-auto my-4 border border-gray-200 rounded"><table className="w-full text-sm">{children}</table></div>,
        thead: ({ children }) => <thead className="bg-gray-50 border-b border-gray-200 text-gray-500 font-medium">{children}</thead>,
        th: ({ children }) => <th className="px-4 py-2 text-left font-medium">{children}</th>,
        td: ({ children }) => <td className="px-4 py-2 border-b border-gray-100 text-gray-600 last:border-0">{children}</td>,
        
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          return !inline && match ? (
            <div className="relative my-4 border border-gray-200 rounded-lg overflow-hidden bg-gray-50/30">
              <div className="flex justify-between items-center px-3 py-1.5 border-b border-gray-100 bg-white">
                <span className="text-xs text-gray-400 font-mono">{match[1]}</span>
                <CodeCopyBtn text={String(children)} />
              </div>
              <SyntaxHighlighter
                {...props}
                style={oneLight}
                language={match[1]}
                PreTag="div"
                customStyle={{ margin: 0, background: 'transparent', fontSize: '13px' }}
              >
                {String(children).replace(/\n$/, "")}
              </SyntaxHighlighter>
            </div>
          ) : (
            <code {...props} className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-[13px] font-mono">
              {children}
            </code>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
});
MarkdownContent.displayName = "MarkdownContent";

/* --- Main Component --- */
export default function GeminiChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await userApi.geminiChat(userMsg.content);
      const content = typeof res === 'string' ? res : (res.assistant || res.message || JSON.stringify(res));
      setMessages((prev) => [...prev, { role: "assistant", content }]);
    } catch {
      toast.error("Connection failed");
      setMessages((prev) => [...prev, { role: "assistant", content: "Error connecting to the model." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    /* 1. HEIGHT CONSTRAINT & FLEX COLUMN
       - h-[85vh] sets the total height.
       - flex-col ensures we stack: Header (Top) -> Chat (Middle) -> Input (Bottom).
    */
    <Card className="flex flex-col  bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden font-sans">
      
      {/* --- 1. Fixed Header --- */}
      <div className="flex-none flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-white/80 backdrop-blur-sm z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-black text-white rounded-full flex items-center justify-center">
            <Cpu size={16} />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm text-gray-900 tracking-tight">Gemini Assistant</span>
            <span className="text-[11px] text-gray-400 font-medium">Swiss Design System</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`block w-1.5 h-1.5 rounded-full ${isLoading ? "bg-orange-500 animate-pulse" : "bg-green-500"}`} />
          <span className="text-[10px] font-medium text-gray-400 uppercase tracking-widest">
            {isLoading ? "Thinking" : "Ready"}
          </span>
        </div>
      </div>

      {/* --- 2. Scrollable Chat Area --- */}
      {/* CRITICAL FIX:
          - `flex-1`: Takes up all available space between Header and Input.
          - `min-h-0`: Prevents the flex child from refusing to shrink below its content size (fixing the no-scroll bug).
          - `w-full`: Ensures full width.
      */}
      <ScrollArea className="flex-1 min-h-0 bg-white w-full ">
        <div className="flex flex-col space-y-8 p-6">
          
          {messages.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center opacity-30 mt-12">
              <div className="w-12 h-12 border border-gray-200 rounded-xl flex items-center justify-center mb-4">
                <Cpu size={24} className="text-black" />
              </div>
              <p className="text-sm text-gray-500 font-medium">How can I help you today?</p>
            </div>
          )}

          {messages.map((msg, i) => {
            const isUser = msg.role === "user";
            const isJson = !isUser && isJsonString(msg.content);

            return (
              <div key={i} className={`flex w-full ${isUser ? "justify-end" : "justify-start"} group`}>
                
                {/* Avatar for Bot */}
                {!isUser && (
                  <div className="w-6 h-6 flex-shrink-0 mr-4 mt-1 text-black">
                    <Cpu size={20} strokeWidth={1.5} />
                  </div>
                )}

                <div className={`max-w-[85%] ${isUser ? "ml-12" : "mr-12"}`}>
                  {/* Name Label (Bot only) */}
                  {!isUser && (
                    <div className="text-[11px] text-gray-400 font-medium mb-1 ml-1 uppercase tracking-wider">
                      AI Model
                    </div>
                  )}

                  {/* Message Content */}
                  <div
                    className={`
                      text-[14px] px-4 py-3 rounded-2xl
                      ${isUser 
                        ? "bg-gray-100 text-gray-900 rounded-tr-sm"
                        : "bg-transparent text-gray-800 p-0 rounded-none"
                      }
                    `}
                  >
                    {isJson ? (
                      <JsonBlock text={msg.content} />
                    ) : (
                      isUser ? (
                        <div className="whitespace-pre-wrap leading-6">{msg.content}</div>
                      ) : (
                        <MarkdownContent content={msg.content} />
                      )
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex w-full justify-start">
               <div className="w-6 h-6 flex-shrink-0 mr-4 mt-1 text-black">
                  <Cpu size={20} strokeWidth={1.5} />
               </div>
               <div className="mt-2">
                 <LoadingDots />
               </div>
            </div>
          )}
          
          {/* Invisible element to scroll to */}
          <div ref={scrollRef} className="h-1" />
        </div>
      </ScrollArea>

      {/* --- 3. Fixed Input Area --- */}
      <div className="flex-none p-6 pt-2 bg-white">
        <div className="relative flex items-end gap-2 border border-gray-200 rounded-xl bg-white shadow-[0_2px_10px_rgba(0,0,0,0.02)] hover:border-gray-300 transition-colors p-1.5 focus-within:ring-1 focus-within:ring-black focus-within:border-black">
          <Input
            className="flex-1 min-h-[44px] border-none shadow-none focus-visible:ring-0 bg-transparent text-sm placeholder:text-gray-400 py-3 pl-3"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !isLoading && sendMessage()}
            disabled={isLoading}
            autoFocus
          />
          <Button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            size="icon"
            className={`
              h-8 w-8 rounded-lg mb-1 mr-1 transition-all duration-200
              ${(!input.trim() || isLoading)
                ? "bg-gray-100 text-gray-300 hover:bg-gray-100"
                : "bg-black text-white hover:bg-gray-800 hover:scale-105 active:scale-95"
              }
            `}
          >
            {isLoading ? (
              <Circle className="animate-spin text-gray-400" size={14} />
            ) : (
              <ArrowUp size={16} strokeWidth={2.5} />
            )}
          </Button>
        </div>
        <div className="text-center mt-3">
           <p className="text-[10px] text-gray-400">Powered by Gemini • AI can make mistakes.</p>
        </div>
      </div>
    </Card>
  );
}