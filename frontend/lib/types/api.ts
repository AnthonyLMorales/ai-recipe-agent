// API request/response types matching backend schema

export interface CookingQueryRequest {
  query: string;
  thread_id?: string;
}

export interface CookingQueryResponse {
  response: string;
  metadata: {
    query_type?: string;
    is_relevant?: boolean;
    dish?: string;
  };
  thread_id: string;
}

export interface ApiError {
  detail: string;
  status?: number;
}
