// 手機本機儲存：歷史紀錄與後端網址（AsyncStorage）
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { AnalyzeResult } from './api';

export interface HistoryItem {
  id: string;
  createdAt: number;
  imageUri: string;     // 範例圖是後端網址；上傳的是手機本機路徑
  label: string;
  result: AnalyzeResult;
}

const HISTORY_KEY = 'echolvh.history.v1';
const SERVER_KEY = 'echolvh.server.v1';

export async function loadHistory(): Promise<HistoryItem[]> {
  try {
    const s = await AsyncStorage.getItem(HISTORY_KEY);
    return s ? JSON.parse(s) : [];
  } catch {
    return [];
  }
}

export async function addHistory(item: HistoryItem) {
  const list = (await loadHistory()).filter((h) => h.id !== item.id);
  list.unshift(item);
  try {
    await AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, 20)));
  } catch {}
}

export async function updateHistory(id: string, result: AnalyzeResult) {
  const list = await loadHistory();
  const i = list.findIndex((h) => h.id === id);
  if (i >= 0) {
    list[i] = { ...list[i], result };
    try {
      await AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(list));
    } catch {}
  }
}

export async function loadServer(): Promise<string | null> {
  try {
    return await AsyncStorage.getItem(SERVER_KEY);
  } catch {
    return null;
  }
}

export async function saveServer(url: string) {
  try {
    await AsyncStorage.setItem(SERVER_KEY, url);
  } catch {}
}
