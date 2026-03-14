const API_BASE = '/api';

export interface PipelineInputs {
  story: string;
  skills: string;
  audience: string;
  situation: string;
  product: string;
}

export async function runStep(step: string, body: Record<string, unknown>): Promise<unknown> {
  const res = await fetch(`${API_BASE}/pipeline/${step}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `Step ${step} failed`);
  }
  return res.json();
}
