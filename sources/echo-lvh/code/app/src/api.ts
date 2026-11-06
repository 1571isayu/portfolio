// 與 FastAPI 後端溝通。後端網址預設自動偵測：跟 Expo 開發伺服器同一台電腦的 8000 port。
import Constants from 'expo-constants';
import { Platform } from 'react-native';

export type MetricKey = 'IVSd' | 'LVIDd' | 'LVPWd';
export type Point = [number, number];

export interface Report {
  professional: string;
  plain: string;
  source: 'gemini' | 'template';
  model: string | null;
  seconds: number;
  number_check: 'pass' | 'fail';
  fallback_reason?: string;
}

export interface AnalyzeResult {
  measurements_cm: Record<MetricKey, number>;
  rwt: number | null;
  lvh_suspected: boolean;
  thick_walls: MetricKey[];
  rwt_increased: boolean;
  thresholds: { wall_cm: number; rwt: number };
  scale_source: 'dataset' | 'user' | 'estimated';
  confidence?: Record<string, number>;
  low_confidence?: boolean;
  points: Record<'lvpw_outer' | 'lvpw_lvid' | 'lvid_ivs' | 'ivs_outer', Point>;
  image_size: { width: number; height: number };
  content_size?: { width: number; height: number };   // 範例圖：去掉黑邊後的實際範圍
  inference_seconds: number;
  ground_truth_cm: Record<MetricKey, number> | null;
  report?: Report;
}

export interface Sample {
  id: string;
  image_url: string;
  ground_truth_cm: Record<MetricKey, number>;
}

export interface Health {
  status: string;
  model_loaded: boolean;
  gemini_configured: boolean;
  gemini_model: string;
  n_samples: number;
}

export function defaultBaseUrl(): string {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  const host = Constants.expoConfig?.hostUri ?? '';
  const ip = host.split(':')[0];
  return ip ? `http://${ip}:8000` : 'http://192.168.0.10:8000';
}

let baseUrl = defaultBaseUrl();
export const getBaseUrl = () => baseUrl;
export const setBaseUrl = (u: string) => {
  baseUrl = u.trim().replace(/\/+$/, '');
};
export const absUrl = (path: string) => (path.startsWith('http') ? path : `${baseUrl}${path}`);

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 30000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(absUrl(path), { ...init, signal: ctrl.signal });
    if (!res.ok) {
      let msg = `伺服器回應 ${res.status}`;
      try {
        const j = await res.json();
        if (j?.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
      } catch {}
      throw new Error(msg);
    }
    return (await res.json()) as T;
  } catch (e: any) {
    if (e?.name === 'AbortError') throw new Error('連線逾時：請確認後端有啟動，且手機與電腦在同一個 Wi-Fi');
    if (e instanceof TypeError) throw new Error(`連不到後端（${baseUrl}）：請確認後端用 --host 0.0.0.0 啟動，且在同一個 Wi-Fi`);
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export const health = () => request<Health>('/health', {}, 6000);
export const listSamples = (limit = 24) => request<Sample[]>(`/samples?limit=${limit}`);

export function analyzeSample(sampleId: string) {
  const fd = new FormData();
  fd.append('sample_id', sampleId);
  return request<AnalyzeResult>('/analyze', { method: 'POST', body: fd });
}

export async function analyzePhoto(uri: string, mimeType = 'image/jpeg') {
  const fd = new FormData();
  if (Platform.OS === 'web') {
    const blob = await (await fetch(uri)).blob();
    fd.append('file', blob, 'photo.jpg');
  } else {
    // React Native 的 FormData 檔案格式
    fd.append('file', { uri, name: mimeType === 'image/png' ? 'photo.png' : 'photo.jpg', type: mimeType } as any);
  }
  return request<AnalyzeResult>('/analyze', { method: 'POST', body: fd }, 45000);
}

export const makeReport = (r: AnalyzeResult) =>
  request<Report>('/report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(r),
  });

export const askAI = (question: string, result: AnalyzeResult) =>
  request<{ answer: string; source: string }>('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, result }),
  });
