/*
=====================================================

Adaptive Context Intelligence Engine (ACIE)

useChat Hook

=====================================================
*/

import { useEffect, useState } from "react";

import { sendChatMessage } from "../api/client";

const CHAT_STORAGE_KEY = "acie.chat.messages";

function loadSavedMessages() {
    if (typeof window === "undefined") return [];

    try {
        const saved = window.localStorage.getItem(CHAT_STORAGE_KEY);
        const messages = saved ? JSON.parse(saved) : [];
        return Array.isArray(messages)
            ? messages.filter(
                (message) =>
                    ["user", "assistant"].includes(message?.role) &&
                    typeof message?.content === "string"
            ).slice(-200)
            : [];
    } catch {
        return [];
    }
}

function useChat() {

    const [messages, setMessages] = useState(loadSavedMessages);

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState(null);

    useEffect(() => {
        try {
            window.localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
        } catch (storageError) {
            console.warn("Unable to save ACIE chat history:", storageError);
        }
    }, [messages]);

    const sendMessage = async (query) => {

        if (!query.trim()) return null;

        const userMessage = {
            role: "user",
            content: query
        };

        const conversation = messages.slice(-12).map(({ role, content }) => ({
            role,
            content
        }));

        setMessages((prev) => [...prev, userMessage].slice(-200));

        setLoading(true);

        setError(null);

        try {

            const response = await sendChatMessage(query, conversation);

            const aiMessage = {
                role: "assistant",
                content:
                    response.answer ||
                    response.response ||
                    "No response generated."
            };

            setMessages((prev) => [...prev, aiMessage].slice(-200));

            return response;

        } catch (err) {

            console.error(err);

            setError(err.message);

            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content:
                        "Unable to connect with ACIE backend."
                }
            ].slice(-200));

            return null;

        } finally {

            setLoading(false);

        }

    };

    const clearChat = () => {

        setMessages([]);

        setError(null);

    };

    return {

        messages,

        loading,

        error,

        sendMessage,

        clearChat

    };

}

export default useChat;
