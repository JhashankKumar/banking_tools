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
}

/** Every failed API call surfaces as this error (see API_AND_CODE_CONVENTIONS §1.2, §3.2). */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: FieldProblem[];
  readonly requestId: string | null;

  constructor({
    status,
    code,
    message,
    details = [],
    requestId = null,
  }: ApiErrorInit) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

/** A message that is safe to show: the server's for known API errors, the fallback otherwise. */
export function userMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}
