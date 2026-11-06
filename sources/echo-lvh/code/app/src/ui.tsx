import { ReactNode } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View, ViewStyle } from 'react-native';
import { color, font, radius, space } from './theme';

export function Button({ title, onPress, kind = 'primary', disabled, icon }: {
  title: string; onPress: () => void; kind?: 'primary' | 'secondary' | 'ghost'; disabled?: boolean; icon?: string;
}) {
  const bg = kind === 'primary' ? color.primary : kind === 'secondary' ? color.primarySoft : 'transparent';
  const fg = kind === 'primary' ? '#fff' : color.primary;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [s.btn, { backgroundColor: bg, opacity: disabled ? 0.45 : pressed ? 0.85 : 1 },
        kind === 'ghost' && { borderWidth: 1, borderColor: color.line }]}
      accessibilityRole="button"
    >
      <Text style={[s.btnText, { color: fg }]}>{icon ? `${icon}  ` : ''}{title}</Text>
    </Pressable>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  return <View style={[s.card, style]}>{children}</View>;
}

export function Header({ title, onBack, right }: { title: string; onBack?: () => void; right?: ReactNode }) {
  return (
    <View style={s.header}>
      {onBack ? (
        <Pressable onPress={onBack} hitSlop={12} accessibilityRole="button" accessibilityLabel="返回">
          <Text style={s.back}>‹ 返回</Text>
        </Pressable>
      ) : <View style={{ width: 56 }} />}
      <Text style={s.headerTitle} numberOfLines={1}>{title}</Text>
      <View style={{ width: 56, alignItems: 'flex-end' }}>{right}</View>
    </View>
  );
}

export function Badge({ text, tone = 'neutral' }: { text: string; tone?: 'neutral' | 'ok' | 'warn' | 'primary' }) {
  const map = {
    neutral: [color.line, color.muted], ok: [color.okSoft, color.ok],
    warn: [color.warnSoft, color.warn], primary: [color.primarySoft, color.primary],
  } as const;
  const [bg, fg] = map[tone];
  return <View style={[s.badge, { backgroundColor: bg }]}><Text style={[s.badgeText, { color: fg }]}>{text}</Text></View>;
}

export function Loading({ text }: { text: string }) {
  return (
    <View style={s.loading}>
      <ActivityIndicator size="large" color={color.primary} />
      <Text style={[font.small, { marginTop: space(3) }]}>{text}</Text>
    </View>
  );
}

export function Disclaimer() {
  return <Text style={[font.small, { textAlign: 'center', marginTop: space(4) }]}>課程專題成果，非醫療診斷工具。</Text>;
}

const s = StyleSheet.create({
  btn: { minHeight: 52, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', paddingHorizontal: space(5) },
  btnText: { fontSize: 16, fontWeight: '700' },
  card: { backgroundColor: color.surface, borderRadius: radius.lg, padding: space(4), borderWidth: 1, borderColor: color.line },
  header: { height: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: space(4) },
  headerTitle: { ...font.h2, flex: 1, textAlign: 'center' },
  back: { color: color.primary, fontSize: 16, fontWeight: '600', width: 56 },
  badge: { alignSelf: 'flex-start', paddingHorizontal: space(2.5), paddingVertical: space(1), borderRadius: 999 },
  badgeText: { fontSize: 12, fontWeight: '700' },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: space(8) },
});
