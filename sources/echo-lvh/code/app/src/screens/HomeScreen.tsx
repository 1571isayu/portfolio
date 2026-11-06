import { useEffect, useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { getBaseUrl, health, Health, setBaseUrl } from '../api';
import { HistoryItem, saveServer } from '../storage';
import { color, font, radius, space } from '../theme';
import { Badge, Button, Card, Disclaimer } from '../ui';

export default function HomeScreen({ history, onSamples, onPickLibrary, onPickCamera, onOpen }: {
  history: HistoryItem[];
  onSamples: () => void;
  onPickLibrary: () => void;
  onPickCamera: () => void;
  onOpen: (h: HistoryItem) => void;
}) {
  const [status, setStatus] = useState<Health | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [url, setUrl] = useState(getBaseUrl());

  const check = () => {
    setErr(null); setStatus(null);
    health().then(setStatus).catch((e) => setErr(e.message));
  };
  useEffect(check, []);

  const saveUrl = async () => {
    setBaseUrl(url); await saveServer(getBaseUrl()); setEditing(false); check();
  };

  return (
    <ScrollView contentContainerStyle={s.wrap}>
      <View style={s.hero}>
        <Text style={s.kicker}>EchoLVH 小助手</Text>
        <Text style={font.title}>一張超音波圖，{'\n'}看懂心臟的牆有多厚</Text>
        <Text style={[font.body, { color: color.muted, marginTop: space(2) }]}>
          AI 自動量測心室中隔、左心室內徑與後壁，判斷是否疑似左心室肥厚，並寫成看得懂的報告。
        </Text>
      </View>

      <Card style={{ gap: space(3) }}>
        <Button title="用範例圖試試" icon="🫀" onPress={onSamples} />
        <View style={{ flexDirection: 'row', gap: space(3) }}>
          <View style={{ flex: 1 }}><Button title="從相簿選" kind="secondary" onPress={onPickLibrary} /></View>
          <View style={{ flex: 1 }}><Button title="拍照" kind="secondary" onPress={onPickCamera} /></View>
        </View>
        <Text style={font.small}>僅支援胸骨旁長軸切面（PLAX）。上傳的圖片沒有比例尺，公分數值為估計值；範例圖最準確。</Text>
      </Card>

      <Card style={{ marginTop: space(4) }}>
        <View style={s.rowBetween}>
          <Text style={font.h2}>連線狀態</Text>
          <Pressable onPress={() => setEditing((v) => !v)} hitSlop={10}>
            <Text style={s.link}>{editing ? '取消' : '設定'}</Text>
          </Pressable>
        </View>
        {editing ? (
          <View style={{ marginTop: space(3), gap: space(2) }}>
            <Text style={font.small}>後端網址（電腦的 IP，port 8000）</Text>
            <TextInput value={url} onChangeText={setUrl} autoCapitalize="none" autoCorrect={false}
              keyboardType="url" style={s.input} placeholder="http://192.168.x.x:8000" />
            <Button title="儲存並重新連線" onPress={saveUrl} />
          </View>
        ) : (
          <View style={{ marginTop: space(3), gap: space(2) }}>
            <Text style={font.small} numberOfLines={1}>{getBaseUrl()}</Text>
            {status ? (
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space(2) }}>
                <Badge text={status.model_loaded ? '量測模型 ✓' : '量測模型未載入'} tone={status.model_loaded ? 'ok' : 'warn'} />
                <Badge text={status.gemini_configured ? 'Gemini ✓' : 'Gemini 未設定（使用模板）'} tone={status.gemini_configured ? 'ok' : 'neutral'} />
              </View>
            ) : err ? (
              <>
                <Badge text="連不到後端" tone="warn" />
                <Text style={[font.small, { color: color.warn }]}>{err}</Text>
                <Button title="重試" kind="ghost" onPress={check} />
              </>
            ) : <Text style={font.small}>連線中…</Text>}
          </View>
        )}
      </Card>

      {history.length > 0 && (
        <View style={{ marginTop: space(6) }}>
          <Text style={[font.h2, { marginBottom: space(3) }]}>最近的分析</Text>
          {history.slice(0, 6).map((h) => (
            <Pressable key={h.id} onPress={() => onOpen(h)} style={({ pressed }) => [s.hist, pressed && { opacity: 0.8 }]}>
              <Image source={{ uri: h.imageUri }} style={s.thumb} />
              <View style={{ flex: 1 }}>
                <Text style={[font.body, { fontWeight: '600' }]} numberOfLines={1}>{h.label}</Text>
                <Text style={font.small}>
                  IVSd {h.result.measurements_cm.IVSd.toFixed(2)} · LVPWd {h.result.measurements_cm.LVPWd.toFixed(2)} cm
                </Text>
              </View>
              <Badge text={h.result.lvh_suspected ? '疑似增厚' : '未超過門檻'} tone={h.result.lvh_suspected ? 'warn' : 'ok'} />
            </Pressable>
          ))}
        </View>
      )}
      <Disclaimer />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  wrap: { padding: space(4), paddingBottom: space(10) },
  hero: { paddingVertical: space(6), paddingHorizontal: space(1) },
  kicker: { color: color.primary, fontWeight: '700', letterSpacing: 1, marginBottom: space(2) },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  link: { color: color.primary, fontWeight: '600' },
  input: { borderWidth: 1, borderColor: color.line, borderRadius: radius.sm, padding: space(3), fontSize: 15, backgroundColor: color.bg, color: color.ink },
  hist: { flexDirection: 'row', alignItems: 'center', gap: space(3), backgroundColor: color.surface, borderRadius: radius.md, padding: space(3), marginBottom: space(2), borderWidth: 1, borderColor: color.line },
  thumb: { width: 52, height: 52, borderRadius: radius.sm, backgroundColor: '#000' },
});
