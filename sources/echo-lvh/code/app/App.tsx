// EchoLVH 小助手 — 手機 App 入口
// 畫面：首頁 → 範例圖 / 相簿 / 拍照 → 量測結果 → AI 報告 → 問 AI
import { StatusBar } from 'expo-status-bar';
import * as ImagePicker from 'expo-image-picker';
import { useEffect, useState } from 'react';
import { Alert, BackHandler, Modal, Platform, StyleSheet, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { absUrl, analyzePhoto, analyzeSample, Report, Sample, setBaseUrl } from './src/api';
import ChatScreen from './src/screens/ChatScreen';
import HomeScreen from './src/screens/HomeScreen';
import ReportScreen from './src/screens/ReportScreen';
import ResultScreen from './src/screens/ResultScreen';
import SamplesScreen from './src/screens/SamplesScreen';
import { addHistory, HistoryItem, loadHistory, loadServer, updateHistory } from './src/storage';
import { color } from './src/theme';
import { Loading } from './src/ui';

type Route =
  | { name: 'home' }
  | { name: 'samples' }
  | { name: 'result'; id: string }
  | { name: 'report'; id: string }
  | { name: 'chat'; id: string };

export default function App() {
  const [stack, setStack] = useState<Route[]>([{ name: 'home' }]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [current, setCurrent] = useState<HistoryItem | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  const route = stack[stack.length - 1];
  const push = (r: Route) => setStack((s) => [...s, r]);
  const back = () => setStack((s) => (s.length > 1 ? s.slice(0, -1) : s));

  useEffect(() => {
    (async () => {
      const saved = await loadServer();
      if (saved) setBaseUrl(saved);
      setHistory(await loadHistory());
      setReady(true);
    })();
  }, []);

  // Android 返回鍵
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (stack.length > 1) { back(); return true; }
      return false;
    });
    return () => sub.remove();
  }, [stack.length]);

  const finish = async (item: HistoryItem) => {
    setCurrent(item);
    await addHistory(item);
    setHistory(await loadHistory());
    setStack([{ name: 'home' }, { name: 'result', id: item.id }]);
  };

  const fail = (e: any) => {
    const msg = e?.message ?? String(e);
    if (Platform.OS === 'web') window.alert(msg); else Alert.alert('分析失敗', msg);
  };

  const runSample = async (s: Sample, index?: number) => {
    setBusy('AI 正在量測…');
    try {
      const result = await analyzeSample(s.id);
      await finish({ id: `sample-${s.id}`, createdAt: Date.now(), imageUri: absUrl(s.image_url),
        label: `範例圖 ${s.id.slice(0, 8)}`, result });
    } catch (e) { fail(e); } finally { setBusy(null); }
  };

  const runPhoto = async (camera: boolean) => {
    const perm = camera ? await ImagePicker.requestCameraPermissionsAsync() : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) { fail(new Error(camera ? '需要相機權限' : '需要相簿權限')); return; }
    const opts: ImagePicker.ImagePickerOptions = { mediaTypes: ['images'], quality: 0.9 };
    const picked = camera ? await ImagePicker.launchCameraAsync(opts) : await ImagePicker.launchImageLibraryAsync(opts);
    if (picked.canceled || !picked.assets?.length) return;
    const a = picked.assets[0];
    setBusy('上傳並量測中…');
    try {
      const result = await analyzePhoto(a.uri, a.mimeType ?? 'image/jpeg');
      await finish({ id: `photo-${Date.now()}`, createdAt: Date.now(), imageUri: a.uri,
        label: camera ? '拍攝的影像' : '相簿的影像', result });
    } catch (e) { fail(e); } finally { setBusy(null); }
  };

  const open = (h: HistoryItem) => { setCurrent(h); push({ name: 'result', id: h.id }); };

  const onReportReady = async (r: Report) => {
    if (!current) return;
    const updated = { ...current, result: { ...current.result, report: r } };
    setCurrent(updated);
    await updateHistory(updated.id, updated.result);
    setHistory(await loadHistory());
  };

  let screen = null;
  if (!ready) screen = <Loading text="啟動中…" />;
  else if (route.name === 'home')
    screen = <HomeScreen history={history} onSamples={() => push({ name: 'samples' })}
      onPickLibrary={() => runPhoto(false)} onPickCamera={() => runPhoto(true)} onOpen={open} />;
  else if (route.name === 'samples') screen = <SamplesScreen onBack={back} onPick={runSample} />;
  else if (current && route.name === 'result')
    screen = <ResultScreen item={current} onBack={back} onReport={() => push({ name: 'report', id: current.id })}
      onChat={() => push({ name: 'chat', id: current.id })} />;
  else if (current && route.name === 'report')
    screen = <ReportScreen item={current} onBack={back} onChat={() => push({ name: 'chat', id: current.id })} onReportReady={onReportReady} />;
  else if (current && route.name === 'chat') screen = <ChatScreen item={current} onBack={back} />;

  return (
    <SafeAreaProvider>
      <SafeAreaView style={s.root} edges={['top', 'bottom']}>
        <StatusBar style="dark" />
        <View style={s.content}>{screen}</View>
        <Modal visible={!!busy} transparent animationType="fade">
          <View style={s.overlay}>
            <View style={s.overlayBox}><Loading text={busy ?? ''} /></View>
          </View>
        </Modal>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: color.bg },
  content: { flex: 1, width: '100%', maxWidth: 720, alignSelf: 'center' },
  overlay: { flex: 1, backgroundColor: 'rgba(16,35,31,0.35)', alignItems: 'center', justifyContent: 'center' },
  overlayBox: { width: 240, height: 180, backgroundColor: color.surface, borderRadius: 20 },
});
