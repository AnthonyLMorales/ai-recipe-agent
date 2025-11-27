// API client for cooking backend

import type { CookingQueryRequest, CookingQueryResponse, ApiError } from "../types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Sends a cooking query to the backend API
 * @param query - The cooking-related question or request
 * @param threadId - Optional thread ID for conversation continuity
 * @returns Promise with the API response
 * @throws Error with descriptive message on failure
 */
export async function sendCookingQuery(
  query: string,
  threadId?: string
): Promise<CookingQueryResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/cooking`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        thread_id: threadId,
      } as CookingQueryRequest),
    });

    if (!response.ok) {
      // Try to parse error detail from response
      let errorMessage = "Failed to process your request";

      try {
        const errorData: ApiError = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // If JSON parsing fails, use status-based messages
        if (response.status >= 500) {
          errorMessage = "Server error processing your request";
        } else if (response.status >= 400) {
          errorMessage = "Invalid request";
        }
      }

      throw new Error(errorMessage);
    }

    const data: CookingQueryResponse = await response.json();
    return data;
  } catch (error) {
    // Handle network errors
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error("Unable to connect to server. Please ensure the backend is running.");
    }

    // Re-throw other errors
    throw error;
  }
}

/**
 * Sends a cooking query via SSE streaming for real-time progress updates
 * @param query - The cooking question
 * @param threadId - Thread ID for conversation
 * @param onThinking - Callback when node executes
 * @param onComplete - Callback when complete
 * @param onError - Callback on error
 */
export async function sendCookingQueryStream(
  query: string,
  threadId: string,
  onThinking: (node: string, message: string) => void,
  onComplete: (response: string, metadata: Record<string, unknown>, threadId: string) => void,
  onError: (error: string) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const url = new URL(`${API_BASE_URL}/api/cooking/stream`);

    // Use fetch for POST with SSE (EventSource doesn't support POST)
    fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        thread_id: threadId,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("No response body");
        }

        // Read stream
        const readStream = () => {
          reader
            .read()
            .then(({ done, value }) => {
              if (done) {
                resolve();
                return;
              }

              // Decode chunk
              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk.split("\n");

              // Process SSE events
              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  const data = line.slice(6);
                  try {
                    const event = JSON.parse(data);

                    if (event.type === "thinking") {
                      onThinking(event.node, event.message);
                    } else if (event.type === "complete") {
                      onComplete(event.response, event.metadata, event.thread_id);
                      resolve();
                    } else if (event.type === "error") {
                      onError(event.message);
                      reject(new Error(event.message));
                      return;
                    }
                  } catch (e) {
                    console.error("Error parsing SSE event:", e);
                  }
                }
              }

              // Continue reading
              readStream();
            })
            .catch((err) => {
              onError(err.message);
              reject(err);
            });
        };

        readStream();
      })
      .catch((err) => {
        const errorMessage = err instanceof Error ? err.message : "Stream connection failed";
        onError(errorMessage);
        reject(err);
      });
  });
}
