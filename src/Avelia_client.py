#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Avelia standalone TCP client.

Usage:
  python Avelia_client.py
  python Avelia_client.py --host 127.0.0.1 --port 47500

このクライアントはAvelia Coreやpackモジュールを読み込みません。
TCP接続と端末入出力だけを担当します。
"""

import argparse
import configparser
import os
from pathlib import Path
import socket
import sys

DEFAULT_HOST = os.getenv("AVELIA_DAEMON_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("AVELIA_DAEMON_PORT", "47500"))
DEFAULT_CONFIG_FILE = Path(__file__).with_name("avelia_client.conf")


def _load_connection_config(config_path):
    """接続設定をINIファイルから読み込む。"""
    host = DEFAULT_HOST
    port = DEFAULT_PORT

    config_path = Path(config_path)

    if not config_path.is_file():
        return host, port

    config = configparser.ConfigParser()

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            config.read_file(config_file)
    except (OSError, configparser.Error) as exc:
        raise RuntimeError(
            f"設定ファイルを読み込めません: {config_path}: {exc}"
        ) from exc

    if "CONNECTION" not in config:
        return host, port

    section = config["CONNECTION"]

    configured_host = section.get("host", "").strip()
    if configured_host:
        host = configured_host

    try:
        port = section.getint("port", fallback=port)
    except ValueError as exc:
        raise RuntimeError(
            f"設定ファイルのportが不正です: {config_path}"
        ) from exc

    if not 1 <= port <= 65535:
        raise RuntimeError(
            f"設定ファイルのportが範囲外です: {port}"
        )

    return host, port


def _configure_stdio():
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def _interactive_client(sock: socket.socket):
    """
    TCP -> 端末stdout は受信スレッド、端末stdin -> TCP はメインスレッド。

    Windows Console / PowerShell / cmd.exe では、標準入力をワーカースレッドから
    読む構成が不安定になり得るため、キーボード入力は必ずメインスレッドで処理する。
    """
    import threading

    stop = threading.Event()
    output_lock = threading.Lock()

    def receive_loop():
        try:
            while not stop.is_set():
                try:
                    data = sock.recv(65536)
                except (ConnectionResetError, ConnectionAbortedError, OSError):
                    break

                if not data:
                    break

                text = data.decode("utf-8", errors="replace")

                with output_lock:
                    sys.stdout.write(text)
                    sys.stdout.flush()

        finally:
            stop.set()

    receiver = threading.Thread(
        target=receive_loop,
        name="avelia-client-recv",
        daemon=True,
    )
    receiver.start()

    try:
        # 重要: stdinはメインスレッドで読む。
        while not stop.is_set():
            try:
                line = input()
            except EOFError:
                try:
                    sock.shutdown(socket.SHUT_WR)
                except OSError:
                    pass
                break
            except KeyboardInterrupt:
                break

            if stop.is_set():
                break

            payload = (line + "\n").encode("utf-8", errors="replace")

            try:
                sock.sendall(payload)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                break

    finally:
        stop.set()

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            sock.close()
        except OSError:
            pass

        receiver.join(timeout=0.5)


def _run_client(host: str, port: int):
    _configure_stdio()

    with socket.create_connection((host, port), timeout=10) as sock:
        sock.settimeout(None)

        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass

        _interactive_client(sock)


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Avelia standalone TCP client"
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_FILE),
        help=f"接続設定ファイル (default: {DEFAULT_CONFIG_FILE})",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="接続先ホスト。指定時は設定ファイルより優先",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="接続先ポート。指定時は設定ファイルより優先",
    )
    return parser


def main():
    args = _build_parser().parse_args()

    try:
        host, port = _load_connection_config(args.config)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)

    # コマンドライン引数を最優先する。
    if args.host is not None:
        host = args.host

    if args.port is not None:
        if not 1 <= args.port <= 65535:
            print(
                f"portが範囲外です: {args.port}",
                file=sys.stderr,
            )
            raise SystemExit(2)
        port = args.port

    print(
        f"[Avelia Client] 接続先: {host}:{port}",
        file=sys.stderr,
    )

    try:
        _run_client(host, port)
    except ConnectionRefusedError:
        print(
            f"Aveliaへ接続できません: {host}:{port}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except socket.timeout:
        print(
            f"Aveliaへの接続がタイムアウトしました: {host}:{port}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except OSError as exc:
        print(
            f"Avelia接続エラー: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
