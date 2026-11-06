import { useEffect, useState } from 'react';
import { Pressable, ScrollView, Share, StyleSheet, Text, View } from 'react-native';
import { makeReport, Report } from '../api';
import { HistoryItem } from '../storage';
import { color, font, radius, space } from '../theme';
import { Badge, Button, Card, Disclaimer, Header, Loading } from '../ui';

export default function ReportScreen({ item, onBack, onChat, onReportReady }: {
  item: HistoryItem; onBack: () => void; onChat: () => void; onReportReady: (r: Report) => void;
}) {
  const [report, setReport] = useState<Report | null>(item.result.report ?? null);
  const [err, setErr] = useState<string | null>(null);
  const [mode, setMode] = useState<'plain' | 'professional'>('plain');

  const load = () => {
    setErr(null);
    makeReport(item.result).then((r) => { setReport(r); onReportReady(r); }).catch((e) => setErr(e.message));
  };
  useEffect(() => { if (!report) load(); }, []);

  const text = report ? report[mode] : '';

  return (
    <View style={{ flex: 1 }}>
      <Header title="AI 報告" onBack={onBack} />
      {!report && !err && <Loading text="Gemini 正在撰寫報告…（約 2–5 秒）" />}
      {err && (
        <View style={{ padding: space(4), gap: space(3) }}>
          <Text style={{ color: color.warn }}>{err}</Text>
          <Button title="重試" kind="ghost" onPress={load} />
        </View>
      )}
      {report && (
        <ScrollView contentContainerStyle={{ padding: space(4), paddingBottom: space(10) }}>
          <View style={s.seg} accessibilityRole="tablist">
            {(['plain', 'professional'] as const).map((m) => (
              <Pressable key={m} onPress={() => setMode(m)} style={[s.segItem, mode === m && s.segOn]}
                accessibilityRole="tab" accessibilityState={{ selected: mode === m }}>
                <Text style={[s.segText, mode === m && { color: color.primary }]}>{m === 'plain' ? '白話版' : '專業版'}</Text>
              </Pressable>
            ))}
          </View>

          <Card style={{ marginTop: space(4) }}>
            <Text style={[font.body, { fontSize: 16, lineHeight: 27 }]} selectable>{text}</Text>
          </Card>

          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space(2), marginTop: space(3) }}>
            <Badge text={report.source === 'gemini' ? `由 ${report.model} 產生` : '固定模板（離線）'} tone={report.source === 'gemini' ? 'primary' : 'neutral'} />
            <Badge text={`${report.seconds.toFixed(1)} 秒`} />
            <Badge text={report.number_check === 'pass' ? '數字檢查通過 ✓' : '數字檢查未通過'} tone={report.number_check === 'pass' ? 'ok' : 'warn'} />
          </View>
          {report.source === 'template' && report.fallback_reason && (
            <Text style={[font.small, { marginTop: space(2) }]}>未使用 Gemini：{report.fallback_reason}</Text>
          )}
          <Text style={[font.small, { marginTop: space(3) }]}>
            「數字檢查」會比對報告中的每個數字是否都來自量測結果，避免 AI 編造數值。
          </Text>

          <View style={{ gap: space(3), marginTop: space(6) }}>
            <Button title="問 AI 這份報告" icon="💬" onPress={onChat} />
            <Button title="分享報告" kind="secondary" onPress={() => Share.share({ message: text })} />
          </View>
          <Disclaimer />
        </ScrollView>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  seg: { flexDirection: 'row', backgroundColor: color.line, borderRadius: radius.md, padding: 4 },
  segItem: { flex: 1, paddingVertical: space(2.5), alignItems: 'center', borderRadius: radius.sm },
  segOn: { backgroundColor: color.surface },
  segText: { fontWeight: '700', color: color.muted },
});
