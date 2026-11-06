// 在超音波圖上疊加模型找到的 4 個點與 3 條量測線
import { Image, View } from 'react-native';
import Svg, { Circle, Line } from 'react-native-svg';
import type { AnalyzeResult } from './api';
import { color } from './theme';

export default function Overlay({ uri, result, width }: { uri: string; result: AnalyzeResult; width: number }) {
  const { width: iw, height: ih } = result.image_size;
  const k = width / iw;
  const fullHeight = ih * k;
  const height = (result.content_size?.height ?? ih) * k;   // 裁掉範例圖下方的黑邊
  const p = result.points;
  const P = (pt: [number, number]) => ({ x: pt[0] * k, y: pt[1] * k });
  const a = P(p.lvpw_outer), b = P(p.lvpw_lvid), c = P(p.lvid_ivs), d = P(p.ivs_outer);
  const segs = [
    { from: a, to: b, stroke: color.lvpw },
    { from: b, to: c, stroke: color.lvid },
    { from: c, to: d, stroke: color.ivs },
  ];
  return (
    <View style={{ width, height, borderRadius: 16, overflow: 'hidden', backgroundColor: '#000' }}
      accessible accessibilityLabel="超音波影像，已標出量測點與量測線">
      <Image source={{ uri }} style={{ width, height: fullHeight }} resizeMode="stretch" />
      <Svg width={width} height={fullHeight} style={{ position: 'absolute', left: 0, top: 0 }}>
        {segs.map((sg, i) => (
          <Line key={i} x1={sg.from.x} y1={sg.from.y} x2={sg.to.x} y2={sg.to.y} stroke={sg.stroke} strokeWidth={3} strokeLinecap="round" />
        ))}
        {[a, b, c, d].map((pt, i) => (
          <Circle key={i} cx={pt.x} cy={pt.y} r={5} fill="#fff" stroke="#E11D48" strokeWidth={2} />
        ))}
      </Svg>
    </View>
  );
}
