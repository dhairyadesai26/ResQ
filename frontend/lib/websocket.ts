"use client";

import { useEffect, useState, useRef } from "react";

type WebSocketListener = (data: any) => void;

class WebSocketClient {
  private socket: WebSocket | null = null;
  private listeners: Set<WebSocketListener> = new Set();
  private reconnectTimeout: any = null;
  private pingInterval: any = null;
  private url: string;
  public isConnected: boolean = false;
  private statusListeners: Set<(connected: boolean) => void> = new Set();

  constructor() {
    this.url =
      process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/ws";
  }

  public connect() {
    if (typeof window === "undefined") return;
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        this.isConnected = true;
        this.notifyStatus(true);
        this.startPing();
      };

      this.socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.listeners.forEach((listener) => {
            try {
              listener(payload);
            } catch (err) {
              console.error("Error in WS message listener:", err);
            }
          });
        } catch {
          // Plaintext message (e.g. "pong")
        }
      };

      this.socket.onclose = () => {
        this.isConnected = false;
        this.notifyStatus(false);
        this.stopPing();
        this.scheduleReconnect();
      };

      this.socket.onerror = () => {
        if (this.socket) {
          this.socket.close();
        }
      };
    } catch {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) return;
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, 2500);
  }

  private startPing() {
    this.stopPing();
    this.pingInterval = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send("ping");
      }
    }, 15000);
  }

  private stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  public subscribe(listener: WebSocketListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  public onStatusChange(callback: (connected: boolean) => void): () => void {
    this.statusListeners.add(callback);
    callback(this.isConnected);
    return () => {
      this.statusListeners.delete(callback);
    };
  }

  private notifyStatus(connected: boolean) {
    this.statusListeners.forEach((cb) => cb(connected));
  }
}

export const wsClient = new WebSocketClient();

export function useWebSocket(onMessage?: (payload: any) => void) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    wsClient.connect();

    const unsubStatus = wsClient.onStatusChange((status) => {
      setIsConnected(status);
    });

    const unsubMessage = wsClient.subscribe((data) => {
      if (onMessageRef.current) {
        onMessageRef.current(data);
      }
    });

    return () => {
      unsubStatus();
      unsubMessage();
    };
  }, []);

  return { isConnected };
}

