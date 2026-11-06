// 設計：醫療感但不冰冷。淺色底、一個深青綠主色，肥厚警示用橙紅。
export const color = {
  bg: '#F3F6F5',
  surface: '#FFFFFF',
  ink: '#10231F',
  muted: '#5B6B67',
  line: '#E1E8E6',
  primary: '#0F6E5F',
  primarySoft: '#DDEFEA',
  warn: '#C2410C',
  warnSoft: '#FDEBE1',
  ok: '#15803D',
  okSoft: '#E3F4E8',
  // 三條量測線（與資料探勘時的顏色一致）
  lvpw: '#16A34A',
  lvid: '#D97706',
  ivs: '#C026D3',
};

export const radius = { sm: 8, md: 14, lg: 20 };
export const space = (n: number) => n * 4;

export const font = {
  title: { fontSize: 26, fontWeight: '700' as const, color: color.ink },
  h2: { fontSize: 18, fontWeight: '700' as const, color: color.ink },
  body: { fontSize: 15, lineHeight: 23, color: color.ink },
  small: { fontSize: 13, lineHeight: 19, color: color.muted },
  num: { fontSize: 28, fontWeight: '700' as const, color: color.ink, fontVariant: ['tabular-nums' as const] },
};

export const METRICS = [
  { key: 'IVSd', name: '心室中隔', hint: '左右心室中間的牆', color: color.ivs },
  { key: 'LVIDd', name: '左心室內徑', hint: '心室腔的寬度', color: color.lvid },
  { key: 'LVPWd', name: '左心室後壁', hint: '左心室後方的牆', color: color.lvpw },
] as const;
