# 最終サマリー（日本語）

## 判断ポイント

このタスクを human-controlled commit / merge / completion decision に進めてよいかを確認してください。短い `OK` でも承認として記録できます。

## 最終 diff 概要

- `[変更ファイル / 領域 1]`: `[要約]`
- `[変更ファイル / 領域 2]`: `[要約]`

## 検証結果

| 検証 | 結果 | Evidence |
|------|------|----------|
| `[command or review]` | `[pass/fail/exception]` | `[path/link]` |

## Review findings

| 種別 | 状態 | 内容 |
|------|------|------|
| Blocking | `[resolved/none]` | `[summary]` |
| Non-blocking | `[accepted/follow-up]` | `[summary]` |

## Git governance / Git 運用ルール

- Commits are allowed only on a branch the agent created for the task.
- Commits to other branches, merges, and pushes are forbidden unless explicitly requested.
- Git-untracked product/project files must not be modified without explicit human permission; if not instructed, leave them alone.

## 未解決リスク / follow-up

- `[risk or follow-up, or none]`

## 推奨判断

- `[例: 承認してよい / rework が必要]`

## Artifact policy reminder

`.hermes/tasks/<task-id>/` は task-local working log であり、default では commit しません。Product/project commit が task branch 上で許可される場合でも、この扱いは変わりません。
