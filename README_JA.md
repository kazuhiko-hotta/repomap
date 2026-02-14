name: README_JA
description: repomapプロジェクトの概要とクイックスタートガイド（日本語版）。

# repomap

`repomap`はPythonリポジトリを解析し、トップレベルのレイアウト、インポート、HTTPクライアントの使用状況、およびリテラルURLを要約します。このリポジトリの`repo_map.md`ファイルを提供し、コントリビューターやAIアシスタントがコードの配置場所と関連する部分を素早く理解できるようにします。

## クイックスタート
1. 仮想環境を作成します（オプションですが推奨）: Unixでは`python -m venv .venv && source .venv/bin/activate`、Windowsでは同等のコマンドを実行してください。
2. パッケージとテスト用の追加機能をインストールし、CLIと単体テストの依存関係を取得します: `python -m pip install -e .[testing]`。
3. 以下で説明するCLIを使用して、リポジトリマップを生成または更新します。

### オプション: `venv`の代わりに`uv`を使用
`uv`（https://github.com/uvtools/uv）をビルド/ランタイムのシムとして使用したい場合は、`pip install --user uv`でインストールし、`uv`を通じてCLI/テストを実行して、ツールが隔離された環境を管理できるようにします：

```
uv run python -m pip install -e .[testing]  # uvセッション内で依存関係をインストール
uv run python scripts/run_tests.py           # テストスイートを実行
uv run python scripts/cli.py --dry-run       # リポマップをプレビュー
uv shell                                     # uvが各コマンドを実行するシェルに入る
```

`uv run`は単一のコマンドを実行できますが、`uv shell`は同じ隔離された環境を対話的に使用し続けます。シェルを終了すると、uvは自動的にクリーンアップします。上記のラッパースクリプト（`scripts/run_tests.py`と`scripts/cli.py`）を使用することで、`PYTHONPATH`を手動で設定する必要がなくなります。

## CLIの使用法
パッケージをインストールした後、`python -m repomap`（または`repomap`コンソールスクリプト）を使用して`repo_map.md`を再生成します。CLIは`scripts/cli.py`で使用されているのと同じヘルパーをラップし、いくつかの操作性を追加し、デフォルトで`.gitignore`とビルトインの除外項目（例：`.git`、`.venv`、`__pycache__`、`.idea`）を尊重します。

使用例：
```
python -m repomap              # 現在のディレクトリをスキャンしてrepo_map.mdを上書き
repomap -r ../other-project     # 別のリポジトリルートをターゲットにする
repomap --exclude build --dry-run  # ファイルを変更せずに出力をプレビュー
repomap -o -                   # レポートをファイルではなくstdoutに出力
```

一般的なオプション：
- `-r / --root DIR`: スキャンするディレクトリ（デフォルト：現在の作業ディレクトリ）。
- `-e / --exclude DIR`: 無視するトップレベルディレクトリを追加。
- `-o / --output FILE`: レポートをFILEに書き込む（デフォルトは`repo_map.md`、stdoutに出力するには`-`を使用）。
- `--dry-run`: ファイルを書き込まずにレポートをstdoutに表示。
- `--list-excludes`: 結合された除外セット（デフォルト + `.gitignore` + 任意の`--exclude`値）を表示。
- `--show-defaults`: ビルトインのデフォルト除外項目のみを表示して終了。
- `--quiet`: ファイル書き込み後の最終確認メッセージを抑制。

`scripts/cli.py`の薄いラッパーは、パッケージをインストールせずにCLIを実行できます：これは`src/`が`sys.path`にあることを確認してから`repomap.cli`に移譲するだけです。

生成されたファイルは常に以下を強調表示します：
1. 重要なトップレベルディレクトリ。
2. ディレクトリ別にグループ化されたインポート。
3. HTTPクライアントの使用状況（`requests`、`httpx`、`aiohttp`）。
4. 解析されたPythonファイルで見つかったリテラルURL。

## ライブラリの使用法
`repomap`からヘルパーをインポートします（パッケージソースは`src/repomap`にあります）。より細かな制御が必要な場合、パブリックAPIには`build_exclude_set`、`generate_repo_report`、および`render_repo_map`が含まれます：

```python
from repomap import build_exclude_set, generate_repo_report, render_repo_map
from pathlib import Path

root = Path('.')
exclude = build_exclude_set(root, extra=[])
report = generate_repo_report(root, exclude)
lines = render_repo_map(report, exclude)
print('\n'.join(lines))
```

## テスト
`tests/`にある軽量な単体テストを、何もインストールせずに実行できます：

```
python scripts/run_tests.py
```

テストは現在`repomap`ヘルパーに依存し、`.gitignore`の処理とHTTPインポート/URLの検出をカバーしています。上記のオプションの追加機能をインストールしている場合は、環境に`pytest`が利用可能になった後、`python -m pytest`を実行することもできます。

### インストールなしでのテストとCLIの使用
パッケージをインストールしたくない場合、`scripts/`にあるスクリプトはすでに`src/`を`sys.path`に追加しています。リポジトリルートから以下を実行できます：

```
python scripts/run_tests.py               # 単体テストを実行
python scripts/cli.py                     # インストールせずにrepo_map.mdを再生成
python scripts/cli.py --dry-run           # レポートをプレビュー
python scripts/cli.py --show-defaults     # デフォルトの除外項目を確認
```

`python -m repomap`を直接実行することもできますが、これらのヘルパースクリプトは`PYTHONPATH`を設定する手間を省いてくれます。

## 注記
- `repo_map.md`は人間が読めることを意図しています。インポート状況やディレクトリレイアウトが変更されたときは、再生成してください。
- CLIはすべてのディレクトリレベルの`.gitignore`エントリを尊重します（pathspecによる階層的.gitignore対応）。`*`、`?`、`**/` および否定パターン（`!`）が完全にサポートされています。
- `AGENTS.md`は触らないでください—これはグローバルなエージェントガイドです。
