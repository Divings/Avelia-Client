# Avelia Client

Avelia Client は、Avelia 本体へ TCP ソケット接続し、端末から対話するための軽量クライアントです。

クライアント側では Avelia Core や内部モジュールを直接読み込まず、TCP 接続と標準入出力の中継だけを担当します。

## Features

- Avelia 本体への TCP 接続
- 標準入力をそのまま Avelia へ送信
- Avelia からの応答をリアルタイム表示
- 接続先を設定ファイルから変更可能
- 設定ファイルが存在しない場合はデフォルト設定を使用
- Windows / Linux で利用可能
- 外部 Python ライブラリ不要

## Requirements

- Python 3
- TCP 接続可能な Avelia サーバー

外部依存パッケージはありません。

## Installation

リポジトリをクローンします。

```bash
git clone https://github.com/USERNAME/avelia-client.git
cd avelia-client
```

そのまま Python で実行できます。

```bash
python3 Avelia_client.py
```

Windows の場合:

```powershell
python Avelia_client.py
```

## Configuration

クライアントと同じディレクトリに以下の設定ファイルを配置します。

```text
avelia_client.conf
```

例:

```ini
[CONNECTION]
host = 127.0.0.1
port = 47500
```

### host

Avelia 本体が待ち受けている IP アドレスまたはホスト名です。

例:

```ini
host = 127.0.0.1
```

別PCやVMへ接続する場合:

```ini
host = 192.168.1.100
```

### port

Avelia 本体の TCP 待受ポートです。

デフォルト:

```ini
port = 47500
```

## Default Settings

設定ファイルが存在しない場合は、以下の値が使用されます。

```text
Host: 127.0.0.1
Port: 47500
```

環境変数でも変更できます。

```bash
export AVELIA_DAEMON_HOST=127.0.0.1
export AVELIA_DAEMON_PORT=47500
```

Windows PowerShell:

```powershell
$env:AVELIA_DAEMON_HOST="127.0.0.1"
$env:AVELIA_DAEMON_PORT="47500"
```

## Usage

Avelia 本体を起動した状態でクライアントを実行します。

```bash
python3 Avelia_client.py
```

接続後は通常の Avelia コンソールと同じように操作できます。

```text
User:
こんにちは

Avelia:
こんにちは。
```

入力内容は TCP ソケットを通じて Avelia 本体へ送信されます。

Avelia 側から送信された出力はクライアント端末へリアルタイム表示されます。

## Command Line Options

接続先を直接指定することもできます。

```bash
python3 Avelia_client.py --host 127.0.0.1 --port 47500
```

例:

```bash
python3 Avelia_client.py --host 192.168.56.10 --port 47500
```

コマンドライン引数が指定された場合は、設定ファイルより優先されます。

## Architecture

基本構成:

```text
+----------------------+
|    Avelia Client     |
|                      |
| stdin / stdout       |
+----------+-----------+
           |
           | TCP
           |
+----------v-----------+
|     Avelia Core      |
|                      |
| Authentication       |
| Session              |
| AI Processing        |
+----------------------+
```

クライアントは表示と入力のみを担当し、認証・セッション管理・AI処理などは Avelia 本体側で処理されます。

## Network Security

現在のクライアント通信は通常の TCP ソケット通信を使用します。

そのため、外部ネットワークを経由する場合は、以下のような安全な通信経路の利用を推奨します。

- WireGuard
- VPN
- SSH Tunnel
- 閉域LAN

例:

```text
Avelia Client
      |
      | TCP
      |
   WireGuard
      |
      | Encrypted Tunnel
      |
Avelia Server
```

同一マシン内で使用する場合は、Avelia 本体を以下のように localhost のみにバインドすることを推奨します。

```text
127.0.0.1
```

これにより外部ホストから直接接続されることを防げます。

## Terminal Control

Avelia 本体から ANSI エスケープシーケンスを送信することで、対応端末では画面操作も可能です。

例: 画面消去

```python
sock.sendall(b"\033[2J\033[H")
```

これは一般的な Linux の `clear` や Windows Terminal 上の画面クリアに近い動作になります。

クライアント側で独自制御コマンドを実装することも可能です。

例:

```text
__AVELIA_CLEAR__
```

このような制御メッセージを受信した場合に、クライアント側で画面消去などを実行できます。

## File Structure

例:

```text
avelia-client/
├── Avelia_client.py
├── avelia_client.conf
├── README.md
└── LICENSE
```

RPM パッケージ版の場合:

```text
/usr/bin/avelia-client
/usr/libexec/avelia/Avelia_client.py
/etc/avelia/avelia_client.conf
```

## Troubleshooting

### Connection refused

```text
ConnectionRefusedError
```

Avelia 本体が起動しているか確認してください。

また、IP アドレスとポート番号が一致しているか確認します。

```bash
ss -lntp
```

または:

```bash
netstat -an
```

### Connection timeout

ファイアウォール、VPN、ルーティング設定などを確認してください。

Linux:

```bash
firewall-cmd --list-all
```

### Character encoding issues

Avelia Client は UTF-8 を使用します。

Windows Terminal や PowerShell の使用を推奨します。

### Connection closes immediately

Avelia 本体側のログを確認してください。

認証失敗、セッションエラー、例外などによって接続が終了している可能性があります。

## Design Policy

Avelia Client は可能な限り単純な構造を維持します。

クライアント側へ Avelia 本体の処理を移植せず、

```text
Client = Input / Output
Server = Avelia Core
```

という役割分担を基本としています。

これによりクライアントPC側の依存関係を減らし、Avelia 本体の更新とクライアントの更新を分離できます。

## License

このプロジェクトのライセンスについては `LICENSE` を参照してください。

## Avelia

Avelia は Anvelk Innovations によって開発されている法人運営補助 AI システムです。
