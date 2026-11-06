import { getAnalytics, isSupported } from "firebase/analytics";
import { initializeApp } from "firebase/app";

// 加入這行 @ts-ignore 來忽略 TypeScript 的誤報
// @ts-ignore
import { getReactNativePersistence, initializeAuth } from "firebase/auth";

import AsyncStorage from "@react-native-async-storage/async-storage";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "[已移除]",
  authDomain: "[已移除]",
  projectId: "[已移除]",
  storageBucket: "[已移除]",
  messagingSenderId: "[已移除]",
  appId: "[已移除]",
  measurementId: "[已移除]"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);


// 解決報錯：先檢查環境是否支援，再初始化 Analytics (手機上不會執行，避免崩潰)
let analytics;
isSupported().then((supported) => {
  if (supported) {
    analytics = getAnalytics(app);
  }
});

// 解決警告：使用 initializeAuth 並加入 AsyncStorage，讓使用者的登入狀態可以保留
export const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(AsyncStorage)
});

export const db = getFirestore(app);