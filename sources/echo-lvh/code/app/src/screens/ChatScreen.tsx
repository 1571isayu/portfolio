import { useRef, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { askAI } from '../api';
import { HistoryItem } from '../storage';
import { color, font, radius, space } from '../theme';
import { Header } from '../ui';

type Msg = { role: 'user' | 'ai'; text: string };
const SUGGESTIONS = ['什麼是心室中隔？', 'RWT 是什麼意思？', '這個結果需要擔心嗎？', '左心室肥厚常見的原因有哪些？'];

export default function ChatScreen({ item, onBack }: { item: HistoryItem; onBack: () => void }) {
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: 'ai', text: '你好！我可以用簡單的方式解釋這次的量測結果。想問什麼呢？' },
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const scroller = useRef<ScrollView>(null);

  const send = async (q: string) => {
    const question = q.trim();
    if (!question || busy) return;
    setInput('');
    setMsgs((m) => [...m, { role: 'user', text: question }]);
    setBusy(true);
    try {
      const r = await askAI(question, item.result);
      setMsgs((m) => [...m, { role: 'ai', text: r.answer }]);
    } catch (e: any) {
      setMsgs((m) => [...m, { role: 'ai', text: `抱歉，暫時無法回答：${e.message}` }]);
    } finally {
      setBusy(false);
      setTimeout(() => scroller.current?.scrollToEnd({ animated: true }), 50);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Header title="問 AI" onBack={onBack} />
      <ScrollView ref={scroller} contentContainerStyle={{ padding: space(4), gap: space(3) }}
        onContentSizeChange={() => scroller.current?.scrollToEnd({ animated: true })}>
        {msgs.map((m, i) => (
          <View key={i} style={[s.bubble, m.role === 'user' ? s.user : s.ai]}>
            <Text style={[font.body, m.role === 'user' && { color: '#fff' }]} selectable>{m.text}</Text>
          </View>
        ))}
        {busy && <View style={[s.bubble, s.ai]}><ActivityIndicator color={color.primary} /></View>}
        {msgs.length === 1 && (
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space(2), marginTop: space(2) }}>
            {SUGGESTIONS.map((q) => (
              <Pressable key={q} onPress={() => send(q)} style={s.chip}><Text style={s.chipText}>{q}</Text></Pressable>
            ))}
          </View>
        )}
        <Text style={[font.small, { textAlign: 'center' }]}>AI 回答僅供衛教參考，不能取代醫師診斷。</Text>
      </ScrollView>
      <View style={s.bar}>
        <TextInput value={input} onChangeText={setInput} placeholder="輸入你的問題…" style={s.input}
          onSubmitEditing={() => send(input)} returnKeyType="send" editable={!busy} />
        <Pressable onPress={() => send(input)} disabled={busy || !input.trim()}
          style={[s.send, (busy || !input.trim()) && { opacity: 0.4 }]} accessibilityRole="button" accessibilityLabel="送出">
          <Text style={{ color: '#fff', fontWeight: '700' }}>送出</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  bubble: { maxWidth: '85%', padding: space(3), borderRadius: radius.md },
  ai: { alignSelf: 'flex-start', backgroundColor: color.surface, borderWidth: 1, borderColor: color.line },
  user: { alignSelf: 'flex-end', backgroundColor: color.primary },
  chip: { borderWidth: 1, borderColor: color.primary, borderRadius: 999, paddingHorizontal: space(3), paddingVertical: space(2) },
  chipText: { color: color.primary, fontWeight: '600', fontSize: 14 },
  bar: { flexDirection: 'row', gap: space(2), padding: space(3), borderTopWidth: 1, borderColor: color.line, backgroundColor: color.surface },
  input: { flex: 1, borderWidth: 1, borderColor: color.line, borderRadius: radius.md, paddingHorizontal: space(3), fontSize: 15, minHeight: 44, backgroundColor: color.bg, color: color.ink },
  send: { backgroundColor: color.primary, borderRadius: radius.md, paddingHorizontal: space(4), justifyContent: 'center' },
});
