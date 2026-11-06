import { ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Overlay from '../Overlay';
import { HistoryItem } from '../storage';
import { color, font, METRICS, radius, space } from '../theme';
import { Badge, Button, Card, Disclaimer, Header } from '../ui';

export default function ResultScreen({ item, onBack, onReport, onChat }: {
  item: HistoryItem; onBack: () => void; onReport: () => void; onChat: () => void;
}) {
  const r = item.result;
  const { width } = useWindowDimensions();
  const imgW = Math.min(width, 640) - space(8);
  const thr = r.thresholds.wall_cm;

  return (
    <View style={{ flex: 1 }}>
      <Header title="量測結果" onBack={onBack} />
      <ScrollView contentContainerStyle={s.wrap}>
        <View style={[s.banner, { backgroundColor: r.lvh_suspected ? color.warnSoft : color.okSoft }]}>
          <Text style={[s.bannerTitle, { color: r.lvh_suspected ? color.warn : color.ok }]}>
            {r.lvh_suspected ? '疑似左心室壁增厚' : '心壁厚度未超過門檻'}
          </Text>
          <Text style={font.small}>
            {r.lvh_suspected
              ? `${r.thick_walls.map((k) => METRICS.find((m) => m.key === k)!.name).join('、')}達 ${thr.toFixed(1)} cm（本系統設定的門檻）`
              : `心室中隔與後壁都小於 ${thr.toFixed(1)} cm（本系統設定的門檻）`}
          </Text>
        </View>

        <View style={{ alignItems: 'center', marginTop: space(4) }}>
          <Overlay uri={item.imageUri} result={r} width={imgW} />
          <View style={s.legend}>
            {METRICS.map((m) => (
              <View key={m.key} style={s.legendItem}>
                <View style={[s.swatch, { backgroundColor: m.color }]} />
                <Text style={font.small}>{m.key}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={{ gap: space(3), marginTop: space(4) }}>
          {METRICS.map((m) => {
            const v = r.measurements_cm[m.key];
            const gt = r.ground_truth_cm?.[m.key];
            const over = m.key !== 'LVIDd' && v >= thr;
            return (
              <Card key={m.key} style={s.metric}>
                <View style={[s.bar, { backgroundColor: m.color }]} />
                <View style={{ flex: 1 }}>
                  <Text style={[font.body, { fontWeight: '700' }]}>{m.name} <Text style={font.small}>{m.key}</Text></Text>
                  <Text style={font.small}>{m.hint}</Text>
                  {gt !== undefined && (
                    <Text style={[font.small, { marginTop: space(1) }]}>
                      醫師量 {gt.toFixed(2)} cm · 差 {(Math.abs(v - gt) * 10).toFixed(1)} mm
                    </Text>
                  )}
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={[font.num, over && { color: color.warn }]}>{v.toFixed(2)}</Text>
                  <Text style={font.small}>cm</Text>
                </View>
              </Card>
            );
          })}
          <Card style={s.metric}>
            <View style={[s.bar, { backgroundColor: color.muted }]} />
            <View style={{ flex: 1 }}>
              <Text style={[font.body, { fontWeight: '700' }]}>相對壁厚 <Text style={font.small}>RWT</Text></Text>
              <Text style={font.small}>牆厚度和心室腔大小的比例（不受比例尺影響）</Text>
            </View>
            <Text style={[font.num, r.rwt_increased && { color: color.warn }]}>{r.rwt?.toFixed(2) ?? '—'}</Text>
          </Card>
        </View>

        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space(2), marginTop: space(4) }}>
          <Badge text={r.scale_source === 'dataset' ? '比例尺：資料集' : r.scale_source === 'user' ? '比例尺：使用者提供' : '比例尺：估計值'}
            tone={r.scale_source === 'estimated' ? 'warn' : 'neutral'} />
          <Badge text={`模型 ${(r.inference_seconds * 1000).toFixed(0)} ms`} />
          {r.low_confidence && <Badge text="信心度偏低" tone="warn" />}
        </View>
        {r.scale_source === 'estimated' && (
          <Text style={[font.small, { marginTop: space(2) }]}>上傳的圖片沒有比例尺，公分數值是用資料集平均值估計的，僅供參考；RWT 不受影響。</Text>
        )}
        {r.low_confidence && (
          <Text style={[font.small, { marginTop: space(2), color: color.warn }]}>模型對這張圖沒有把握，可能不是胸骨旁長軸切面或影像品質不佳。</Text>
        )}

        <View style={{ gap: space(3), marginTop: space(6) }}>
          <Button title="看 AI 報告" icon="📝" onPress={onReport} />
          <Button title="問 AI" icon="💬" kind="secondary" onPress={onChat} />
        </View>
        <Disclaimer />
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { padding: space(4), paddingBottom: space(10) },
  banner: { borderRadius: radius.lg, padding: space(4), gap: space(1) },
  bannerTitle: { fontSize: 20, fontWeight: '800' },
  legend: { flexDirection: 'row', gap: space(4), marginTop: space(2) },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: space(1.5) },
  swatch: { width: 14, height: 4, borderRadius: 2 },
  metric: { flexDirection: 'row', alignItems: 'center', gap: space(3), paddingVertical: space(3) },
  bar: { width: 5, alignSelf: 'stretch', borderRadius: 3 },
});
