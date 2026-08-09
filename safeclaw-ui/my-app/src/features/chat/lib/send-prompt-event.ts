/** Cross-component inject: Exec Steer → ChatInput stream (Fail Fast). */

export const SEND_PROMPT_EVENT = "safeclaw:send-prompt";

export type SendPromptDetail = {
  content: string;
};

export function dispatchSendPrompt(content: string): void {
  const trimmed = content.trim();
  if (!trimmed) {
    throw new Error(
      `[dispatchSendPrompt] Empty content (Fail Fast)\n` +
        `  Expected: non-empty user turn to stream`
    );
  }
  window.dispatchEvent(
    new CustomEvent<SendPromptDetail>(SEND_PROMPT_EVENT, {
      detail: { content: trimmed },
    })
  );
}
