# 最終サマリー（日本語）

**Lifecycle:** Materialize / version **`artifacts.final_summary_ja`** per `skills/dev-process/artifacts/SKILL.md` § Numbered task-root artifacts. **Before final review**, fill it with final diff, validation summary, known risks, and review focus. After final review synthesis, **update** it with review findings, unresolved risks, and merge/commit recommendation, then use it immediately **before** `final_human_gate`.

## 判断ポイント

このタスクを human-controlled commit / merge / completion decision に進めてよいかを確認してください。

ただし、`Required human decisions` がある場合は、agent が各判断項目を chat で個別に提示します。短い `OK` は、それらの判断項目が個別に提示され、質問や修正依頼の機会があった後の最終承認としてのみ有効です。

## 最終 diff 概要

- `[変更ファイル / 領域 1]`: `[要約]`
- `[変更ファイル / 領域 2]`: `[要約]`

## 検証結果

| 検証 | 結果 | Evidence |
|------|------|----------|
| `[command or review]` | `[pass/fail/exception]` | `[path/link]` |

## 実際に使った model / reasoning effort（確認）

Hermes は session / model 別の使用状況を出せますが、**dev-process の stage 粒度** は task 側の記録があると追いやすいです。 **`artifacts.plan` の `Model usage record required?`** が **no** のときは、詳細な per-session の証跡は不要であり、下表でも簡潔でよい。

| 項目 | 内容 |
|------|------|
| **review-depth preset（最終）** | `[light \| standard \| deep]` （途中昇格があれば `artifacts.timeline` または **`artifacts.model_usage`** を参照） |
| **reasoning effort** | `[medium / high / unknown + 理由]` 実運用での切り替え要約。**`Model usage record required?` = yes** のときは可能な範囲で session / reasoning evidence を残す。観測できない場合は `unknown` とし、**理由**を同じセルまたは直下に書く（無言の空欄は避ける）。**no** のときは簡潔でよい。 |
| **main model の根拠** | **`Model usage record required?` = no** の例: 「`artifacts.plan` により詳細な model usage 記録は不要」と一言。**yes** の例: `[session id / hermes insights / Hermes Dashboard / 要約・編集済みの証跡のみ]` |
| **補助（auxiliary tier）** | `[必要なら: approval 等が別 tier だった場合のみ]` |

生ログやプロンプト全文を task artifact に貼らない（機微・クレデンシャル・他ユーザデータの可能性）。詳細な行は **`Model usage record required?` = yes** のときのみ **`artifacts.model_usage`** を正としてよい。**no** のときは空の **`artifacts.model_usage`** で矛盾しない。

## Review findings

| 種別 | 状態 | 内容 |
|------|------|------|
| Blocking | `[resolved/none]` | `[summary]` |
| Non-blocking | `[accepted/follow-up]` | `[summary]` |

## Git governance / Git 運用ルール

- All test and product work for the task happened only on the dev-process-created task branch; no pre-existing branch was used unless the human explicitly instructed it.
- Commits to other branches, merges, and pushes are forbidden unless explicitly requested.
- Do not modify **existing** git-untracked product/project files unless explicitly instructed. New product/test files allowed by the approved plan are permitted. `.hermes/tasks/<task-id>/` is exempt from the untracked-product rule but remains uncommitted by default.

## 未解決リスク / follow-up

- `[risk or follow-up, or none]`

## 推奨判断

- `[例: 承認してよい / rework が必要]`

## Artifact policy reminder

`.hermes/tasks/<task-id>/` は task-local working log であり、default では commit しません。product/test の commit が dev-process の task branch 上で行われる場合でも、この扱いは変わりません。
