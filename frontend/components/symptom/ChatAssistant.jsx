"use client";
import { useEffect, useRef, useState } from "react";
import { userApi } from "@/lib/api-services";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Loader2, Send, RefreshCcw, FileText } from "lucide-react";
import { toast } from "sonner";

export default function ChatAssistant() {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const bottomRef = useRef(null);

  const scrollToBottom = () => {
    setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  };

  // Load chat history
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const res = await userApi.getChatHistory();
        setMessages(res.results);
      } catch {
        toast.error("Failed to load chat history.");
      } finally {
        setLoadingHistory(false);
        scrollToBottom();
      }
    };
    loadHistory();
  }, []);

  // Send message or followup
  const sendUserMessage = async (payload, displayText) => {
    const userMsg = {
      role: "user",
      content: displayText,
      created_at: new Date().toISOString(),
    };

    setMessages((m) => [...m, userMsg]);
    scrollToBottom();
    setSending(true);

    try {
      const res = await userApi.sendChatMessage(payload);

      const assistantMsg = {
        role: "assistant",
        content: res.assistant,
        followups: res.followups,
        explanations: res.explanations,
        symptoms: res.symptoms,
        predictions: res.predictions,
        emergency: res.emergency,
        created_at: new Date().toISOString(),
      };

      setMessages((m) => [...m, assistantMsg]);

      if (res.emergency) {
        toast.error("URGENT: Please seek immediate medical attention.");
      }
    } catch (error) {
      toast.error("Failed to send message.");
    } finally {
      setSending(false);
    }

    scrollToBottom();
  };

  // Normal message
  const sendMainMessage = () => {
    if (!text.trim()) return;
    sendUserMessage({ message: text }, text);
    setText("");
  };

  // Follow-up answer
  const answerFollowup = (id, value) => {
    sendUserMessage({ followup: { [id]: value } }, value === "yes" ? "Yes" : "No");
  };

  // Restart consultation
  const restartChat = async () => {
    try {
      await userApi.restartChat();
      toast.success("Consultation restarted.");
      setMessages([]);
    } catch {
      toast.error("Failed to restart.");
    }
  };

  // Fetch summary
  const loadSummary = async () => {
    try {
      const summary = await userApi.getChatSummary();
      toast.info(`Health Score: ${summary.health_score}`);
    } catch (err) {
      toast.error("Failed to load summary.");
    }
  };

  return (
    <Card className="p-4 w-full max-w-3xl mx-auto bg-card border border-border shadow-md">
      <div className="flex justify-between mb-3">
        <h2 className="text-xl font-bold">Health Chat Assistant</h2>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={restartChat}>
            <RefreshCcw className="w-4 h-4 mr-1" /> Restart
          </Button>

          <Button variant="outline" size="sm" onClick={loadSummary}>
            <FileText className="w-4 h-4 mr-1" /> Summary
          </Button>
        </div>
      </div>

      {/* Chat Window */}
      <div className="h-[450px] overflow-y-auto pr-1 space-y-4 bg-background border border-border rounded-md p-3">
        {loadingHistory ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading chat...
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center text-muted-foreground mt-10">
            Start by describing your symptoms.
          </div>
        ) : (
          messages.map((msg, i) => (
            <ChatBubble key={i} msg={msg} onAnswer={answerFollowup} />
          ))
        )}

        {sending && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 mt-4">
        <Input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe your symptoms..."
          onKeyDown={(e) => e.key === "Enter" && sendMainMessage()}
          className="flex-1"
        />

        <Button
          onClick={sendMainMessage}
          disabled={!text.trim() || sending}
          className="flex items-center gap-2"
        >
          {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Send
        </Button>
      </div>
    </Card>
  );
}

/* CHAT BUBBLE */
function ChatBubble({ msg, onAnswer }) {
  const isUser = msg.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap shadow 
        ${isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground border"}`}
      >
        {msg.content}

        {/* Follow-up buttons */}
        {!isUser && msg.followups?.length > 0 && (
          <div className="mt-3 space-y-2">
            {msg.followups.map((f) => (
              <div key={f.id} className="flex gap-2">
                <p className="text-sm font-medium">{f.question}</p>

                <Button size="sm" onClick={() => onAnswer(f.id, "yes")}>Yes</Button>
                <Button size="sm" variant="secondary" onClick={() => onAnswer(f.id, "no")}>
                  No
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Explanations */}
        {!isUser && msg.explanations?.length > 0 && (
          <div className="mt-3 space-y-3">
            {msg.explanations.map((exp, i) => (
              <div key={i} className="bg-white border rounded-lg p-3 shadow-sm">
                <p className="font-semibold text-blue-700">
                  {exp.disease} — {exp.confidence}%
                </p>

                {exp.summary && <p className="text-sm text-gray-600 mt-1">{exp.summary}</p>}

                <p className="mt-2 text-sm font-semibold">Matched Symptoms:</p>
                <ul className="text-sm text-gray-700 list-disc ml-5">
                  {exp.matched_symptoms.map((ms, j) => (
                    <li key={j}>{ms.name} (Weight {ms.weight}, Severity {ms.user_severity})</li>
                  ))}
                </ul>

                <p className="text-xs text-gray-500 mt-1">
                  Contribution: {exp.contribution_percent}%
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* TYPING INDICATOR */
function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-muted-foreground pl-2">
      <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" />
      <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0.15s" }} />
      <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
    </div>
  );
}
