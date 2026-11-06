# sources/：作品的原始資料（資料集）

每個資料夾是一件作品的原始資料，作品頁 `works/<slug>.html` 的內容只能根據這裡寫。
規則見根目錄 `CLAUDE.md` 第 6 節。

| 資料夾 | 作品 | 內容 |
| --- | --- | --- |
| `echo-lvh/` | EchoLVH 小助手 | 程式碼、每週紀錄、評估報告 |
| `handover-engine/` | 接棒引擎 | 程式碼、README |
| `pin-deal/` | PinDeal | 程式碼、AGENTS.md、設計計畫、架構圖 |
| `tabi-tabi/` | TabiTabi | 程式碼 |

每個資料夾都有 `SOURCE.md`，寫明資料從哪裡來、哪些檔案被排除或遮蔽、作者另外提供的背景資訊。
`code/` 是匯入時的快照，**不要修改**。要更新就整份重新匯入，並更新 `SOURCE.md`。
