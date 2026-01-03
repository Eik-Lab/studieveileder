"use client";

import { useState, useRef, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Bot, User, AlertCircle } from "lucide-react";
import { apiClient, isTimeoutError } from "@/lib/api-client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number; 
}

const suggestedQuestions = [
  "Hvordan søker jeg om permisjon?",
  "Når er fristen for semesterregistrering?",
  "Hvor finner jeg timeplan?",
  "Hva er kravene for bacheloroppgave?"
];

export default function Advisor() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hei! Jeg er NMBU sin studieveileder. Hvordan kan jeg hjelpe deg i dag?",
      timestamp: Date.now()
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;
    setShowSuggestions(false);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: Date.now()
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
      const data = await apiClient.post<{ answer: string }>(
        "/api/chat",
        { query: content },
        { timeout: 10000 } 
      );

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer || "Beklager, ingen svar tilgjengelig.",
        timestamp: Date.now()
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: isTimeoutError(err)
          ? "Forespørselen tok for lang tid. Prøv igjen med et enklere spørsmål."
          : "Kunne ikke koble til backend. Prøv igjen senere.",
        timestamp: Date.now()
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString("no-NO", { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      {/* Main content area */}
      <main className="flex-1 relative">
        {/* Centered chat container */}
        <div className="container mx-auto px-4 py-8 max-w-8xl">
          {/* Warning box on mobile only */}
          <div className="lg:hidden mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-900 mb-1">Under utvikling</h3>
              <p className="text-sm text-amber-800">
                Dette er en demo-veileder. Kontakt studieavdelingen:{" "}
                <a href="mailto:studieveiledning@nmbu.no" className="underline hover:text-amber-900">
                  studieveiledning@nmbu.no
                </a>{" "}
                eller besøk{" "}
                <a href="/kontakt" className="underline hover:text-amber-900">
                  kontaktsiden
                </a>.
              </p>
            </div>
          </div>

          <Card className="flex flex-col overflow-hidden shadow-lg" style={{ minHeight: 'calc(100vh - 200px)' }}>
            <CardHeader className="gradient-hero text-white rounded-t-lg">
              <CardTitle className="text-2xl md:text-3xl">Studieveileder</CardTitle>
              <CardDescription className="text-white/90">
                Still spørsmål om studier, eksamener og studentliv
              </CardDescription>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {message.role === "assistant" && (
                      <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                        <Bot className="w-6 h-6 text-primary-foreground" />
                      </div>
                    )}

                    <div
                      className={`max-w-[70%] rounded-lg p-4 ${
                        message.role === "user"
                          ? "bg-secondary text-secondary-foreground rounded-br-none"
                          : "bg-muted text-foreground rounded-bl-none"
                      }`}
                    >
                      <p className="text-sm md:text-base whitespace-pre-line">{message.content}</p>
                      <span className="text-xs opacity-70 mt-2 block">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>

                    {message.role === "user" && (
                      <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                        <User className="w-6 h-6 text-secondary-foreground" />
                      </div>
                    )}
                  </div>
                ))}

                {isTyping && (
                  <div className="flex gap-3 justify-start">
                    <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                      <Bot className="w-6 h-6 text-primary-foreground" />
                    </div>
                    <div className="bg-muted rounded-lg rounded-bl-none p-4">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                        <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                        <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </div>
                )}

                {showSuggestions && messages.length === 1 && (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Foreslåtte spørsmål:</p>
                    <div className="flex flex-wrap gap-2">
                      {suggestedQuestions.map((question) => (
                        <Button
                          key={question}
                          variant="outline"
                          size="sm"
                          onClick={() => handleSendMessage(question)}
                          className="text-left h-auto py-2 px-3"
                        >
                          {question}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              <div className="border-t border-border p-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Skriv ditt spørsmål her..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1"
                  />
                  <Button
                    onClick={() => handleSendMessage(inputValue)}
                    disabled={!inputValue.trim()}
                  >
                    Send
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>

      <Footer />
    </div>
  );
}