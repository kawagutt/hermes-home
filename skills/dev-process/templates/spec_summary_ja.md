# 仕様サマリー（日本語）

## 判断ポイント

この **`artifacts.spec`**（`state.yaml` に記録されたファイル名）の内容で plan stage に進めてよいかを確認してください。短い `OK` でも承認として記録できます。

## ゴール

- `[このタスクで達成することを簡潔に記載]`

## 非ゴール

- `[今回やらないことを記載]`

## 成功条件

- `[検証可能な完了条件 1]`
- `[検証可能な完了条件 2]`

## 主なリスク

| リスク | 対応 / 判断点 |
|--------|----------------|
| `[risk]` | `[mitigation or required human decision]` |

## 人間に確認してほしいこと

- [ ] goal / non-goal が意図どおりか
- [ ] success criteria が十分か
- [ ] risk / required decisions が受け入れ可能か

## 次のアクション

承認後、agent は **`artifacts.human_spec_gate`**（`state.yaml` のパス）に approval/comments を記録し、plan stage に進みます。Material spec change が必要なコメントがある場合、spec 更新と必要な spec review の後、再度 confirmation を求めます。
