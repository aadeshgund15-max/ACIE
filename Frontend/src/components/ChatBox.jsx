/*
=====================================================

Adaptive Context Intelligence Engine (ACIE)

ChatBox Component

=====================================================
*/

import { useEffect, useRef, useState } from "react";

import {
    Send,
    User,
    Bot,
    Loader2,
    Plus
} from "lucide-react";

import useChat from "../hooks/useChat";

function ChatBox({ onTraceUpdate }) {

    const [message, setMessage] = useState("");
    const bottomRef = useRef(null);

    const {
        messages,
        loading,
        sendMessage,
        clearChat
    } = useChat();

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const handleSend = async () => {

        if (!message.trim() || loading) return;

        const query = message.trim();

        setMessage("");

        try {

            const response = await sendMessage(query);

            if (response?.execution) {
                onTraceUpdate?.(response.execution);
            }

        } catch (error) {

            console.error("Chat Error:", error);

        }

    };

    const handleKeyDown = (event) => {

        if (event.key === "Enter" && !event.shiftKey) {

            event.preventDefault();

            handleSend();

        }

    };

    return (

        <div className="chat-box">

            <div className="chat-toolbar">
                <span>{messages.length ? "Conversation" : "New conversation"}</span>
                <button
                    type="button"
                    className="new-chat-button"
                    onClick={() => {
                        clearChat();
                        onTraceUpdate?.([]);
                    }}
                    disabled={loading || messages.length === 0}
                >
                    <Plus size={16} />
                    New chat
                </button>
            </div>

            <div className="chat-messages">

                {messages.length === 0 && (

                    <div className="empty-chat">

                        <Bot size={40} />

                        <h2>Ask ACIE Anything</h2>

                        <p>
                            Adaptive Context Intelligence Engine
                        </p>

                    </div>

                )}

                {messages.map((msg, index) => (

                    <div
                        key={index}
                        className={
                            msg.role === "user"
                                ? "message user"
                                : "message assistant"
                        }
                    >

                        {msg.role === "user"
                            ? <User size={18} />
                            : <Bot size={18} />
                        }

                        <div className="message-content">

                            <p>{msg.content}</p>

                        </div>

                    </div>

                ))}

                {loading && (

                    <div className="message assistant">

                        <Loader2
                            className="spin"
                            size={18}
                        />

                        <p>ACIE is thinking...</p>

                    </div>

                )}

                <div ref={bottomRef} />

            </div>

            <div className="chat-composer">

                <textarea
                    placeholder="Ask ACIE anything..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={loading}
                    rows={1}
                    aria-label="Message ACIE"
                />

                <button
                    onClick={handleSend}
                    disabled={loading || !message.trim()}
                    aria-label="Send message"
                    title="Send message"
                >

                    <Send size={18} />

                </button>

            </div>

        </div>

    );

}

export default ChatBox;
