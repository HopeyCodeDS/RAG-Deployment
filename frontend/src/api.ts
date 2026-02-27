const API_BASE = import.meta.env.VITE_API_URL as string;

if (!API_BASE) {
  console.warn(
    "[rag-api] VITE_API_URL is not set. API calls will fail. " +
      "Create a .env file with VITE_API_URL=<your-api-url>"
  );
}

export interface QueryRequest {
  query_text: string;
}

export interface QueryResponse {
  query_text: string;
  response_text: string;
  sources: string[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function submitQuery(queryText: string): Promise<QueryResponse> {
  const trimmed = queryText.trim();
  if (trimmed.length === 0) {
    throw new ApiError("Query cannot be empty.");
  }
  if (trimmed.length > 1000) {
    throw new ApiError("Query must be 1000 characters or fewer.");
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/submit_query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_text: trimmed } satisfies QueryRequest),
    });
  } catch {
    throw new ApiError(
      "Could not reach the server. Check your network connection and try again."
    );
  }

  if (!response.ok) {
    let detail = `Server error (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body.detail)) {
        detail = body.detail
          .map((d: { msg: string }) => d.msg)
          .join("; ");
      }
    } catch {
      // body was not JSON — keep the generic message
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as QueryResponse;
}
