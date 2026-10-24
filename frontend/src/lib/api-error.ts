export interface FieldProblem {
  field: string;
  message: string;
}

interface ApiErrorInit {
  status: number;
  code: string;
  message: string;
  details?: FieldProblem[];
  requestId?: string | null;
  /** Seconds until a retry may succeed (from Retry-After on 429), else null. */
  retryAfter?: number | null;
}

/** Every failed API call surfaces as this error (see API_AND_CODE_CONVENTIONS §1.2, §3.2). */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: FieldProblem[];
  readonly requestId: string | null;
  readonly retryAfter: number | null;

  constructor({
    status,
    code,
    message,
    details = [],
    requestId = null,
    retryAfter = null,
  }: ApiErrorInit) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
    this.retryAfter = retryAfter;
  }
}

/**
 * Every failure from the HTTP clients is already an ApiError; anything else reaching a catch
 * block is a bug, so it gets a generic message rather than its internal text.
 */
export function asApiError(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError({
        status: 0,
        code: "UNEXPECTED_ERROR",
        message: "Something went wrong.",
      });
}

/** A message that is safe to show: the server's for known API errors, the fallback otherwise. */
export function userMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}
