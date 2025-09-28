"use client";

/**
 * @author: @kokonutui
 * @description: AI Message Input
 * @version: 1.0.0
 * @date: 2025-06-26
 * @license: MIT
 * @website: https://kokonutui.com
 * @github: https://github.com/kokonut-labs/kokonutui
 */

import { Paperclip, Send } from "lucide-react";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useAutoResizeTextarea } from "@/hooks/use-auto-resize-textarea";

interface AIMessageInputProps {
    onSendMessage: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
}

export default function AIMessageInput({ onSendMessage, disabled = false, placeholder = "Type your message..." }: AIMessageInputProps) {
    const [value, setValue] = useState("");
    const { textareaRef, adjustHeight } = useAutoResizeTextarea({
        minHeight: 52,
        maxHeight: 200,
    });
    const [isFocused, setIsFocused] = useState(false);

    const handleSubmit = () => {
        if (value.trim() && !disabled) {
            onSendMessage(value.trim());
            setValue("");
            adjustHeight(true); 
        }
    };

    const handleFocus = () => {
        setIsFocused(true);
    };

    const handleBlur = () => {
        setIsFocused(false);
    };

    const handleContainerClick = () => {
        if (textareaRef.current) {
            textareaRef.current.focus();
        }
    };

    return (
        <div className="w-full">
            <div className="relative w-full">
                <div
                    role="textbox"
                    tabIndex={0}
                    aria-label="Message input container"
                    className={cn(
                        "relative flex flex-col rounded-xl transition-all duration-200 w-full text-left cursor-text",
                        "ring-1 ring-black/10 dark:ring-white/10",
                        isFocused && "ring-black/20 dark:ring-white/20",
                        disabled && "opacity-50 cursor-not-allowed"
                    )}
                    onClick={handleContainerClick}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                            handleContainerClick();
                        }
                    }}
                >
                    <div className="overflow-y-auto max-h-[200px]">
                        <Textarea
                            value={value}
                            placeholder={placeholder}
                            disabled={disabled}
                            className="w-full rounded-xl rounded-b-none px-4 py-3 bg-black dark:bg-secondary-foreground border-none dark:text-white placeholder:text-black/70 dark:placeholder:text-white/70 resize-none focus-visible:ring-0 leading-[1.2]"
                            ref={textareaRef}
                            onFocus={handleFocus}
                            onBlur={handleBlur}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit();
                                }
                            }}
                            onChange={(e) => {
                                setValue(e.target.value);
                                adjustHeight();
                            }}
                        />
                    </div>

                    <div className="h-12 bg-black/5 dark:bg-secondary-foreground rounded-b-xl">
                        <div className="absolute left-3 bottom-3 flex items-center gap-2">
                            <label className="cursor-pointer rounded-lg p-2 bg-black/5 dark:bg-white/5">
                                <input type="file" className="hidden" />
                                <Paperclip className="w-4 h-4 text-black/40 dark:text-white/40 hover:text-black dark:hover:text-white transition-colors" />
                            </label>
                        </div>
                        <div className="absolute right-3 bottom-3">
                            <button
                                type="button"
                                onClick={handleSubmit}
                                disabled={disabled || !value.trim()}
                                className={cn(
                                    "rounded-lg p-2 transition-colors",
                                    value.trim() && !disabled
                                        ? "bg-sky-500/15 text-sky-500 hover:bg-sky-500/25"
                                        : "bg-black/5 dark:bg-white/5 text-black/40 dark:text-white/40 cursor-not-allowed"
                                )}
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
