import { useEffect, useState } from 'react';
import { FlatList, Image, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { absUrl, listSamples, Sample } from '../api';
import { color, font, radius, space } from '../theme';
import { Button, Header, Loading } from '../ui';

export default function SamplesScreen({ onBack, onPick }: { onBack: () => void; onPick: (s: Sample) => void }) {
  const [items, setItems] = useState<Sample[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const { width } = useWindowDimensions();
  const cols = width > 700 ? 4 : 2;
  const size = (Math.min(width, 900) - space(4) * 2 - space(3) * (cols - 1)) / cols;

  const load = () => { setErr(null); listSamples(24).then(setItems).catch((e) => setErr(e.message)); };
  useEffect(load, []);

  return (
    <View style={{ flex: 1 }}>
      <Header title="選一張範例圖" onBack={onBack} />
      <Text style={[font.small, { paddingHorizontal: space(4), marginBottom: space(3) }]}>
        這些是測試資料，模型訓練時沒看過，而且附有醫師量測值可以對照。
      </Text>
      {err ? (
        <View style={{ padding: space(4), gap: space(3) }}>
          <Text style={{ color: color.warn }}>{err}</Text>
          <Button title="重試" kind="ghost" onPress={load} />
        </View>
      ) : !items ? <Loading text="載入範例圖…" /> : (
        <FlatList
          data={items}
          key={cols}
          numColumns={cols}
          keyExtractor={(it) => it.id}
          contentContainerStyle={{ paddingHorizontal: space(4), paddingBottom: space(8), gap: space(3) }}
          columnWrapperStyle={{ gap: space(3) }}
          renderItem={({ item, index }) => {
            const gt = item.ground_truth_cm;
            const thick = Math.max(gt.IVSd, gt.LVPWd) >= 1.1;
            return (
              <Pressable onPress={() => onPick(item)} style={({ pressed }) => [s.tile, { width: size }, pressed && { opacity: 0.8 }]}
                accessibilityRole="button" accessibilityLabel={`範例 ${index + 1}`}>
                <Image source={{ uri: absUrl(item.image_url) }} style={{ width: size - 2, height: size - 2, backgroundColor: '#000' }} />
                <View style={{ padding: space(2) }}>
                  <Text style={[font.small, { color: color.ink, fontWeight: '600' }]}>範例 {index + 1}</Text>
                  <Text style={font.small}>醫師：IVSd {gt.IVSd.toFixed(2)} cm</Text>
                  <Text style={[font.small, { color: thick ? color.warn : color.ok }]}>{thick ? '牆偏厚' : '未超過門檻'}</Text>
                </View>
              </Pressable>
            );
          }}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  tile: { backgroundColor: color.surface, borderRadius: radius.md, overflow: 'hidden', borderWidth: 1, borderColor: color.line },
});
