"use client";

import { useEffect, useState, useRef } from "react";

type WebSocketListener = (data: any) => void;

export function resolveWebSocketUrl(): string {
  // 1. Try explicit NEXT_PUBLIC_WS_URL
  let url = process.env.NEXT_PUBLIC_WS_URL?.trim();

  // 2. If not found, try deriving from NEXT_PUBLIC_API_URL
  if (!url) {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
    if (apiUrl) {
      url = apiUrl
        .replace(/^http:\/\//i, "ws://")
        .replace(/^https:\/\//i, "wss://");
    }
  }

  // 3. Fallback to local development if in local browser or SSR
  if (!url) {
    if (typeof window !== "undefined") {
      if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
        console.warn(
          "[ResQ Web] NEXT_PUBLIC_WS_URL or NEXT_PUBLIC_API_URL is missing. In Vercel, set NEXT_PUBLIC_API_URL and Redeploy."
        );
      }
    }
    return "ws://127.0.0.1:8000/ws";
  }

  // 4. Sanitize scheme: https -> wss, http -> ws
  if (url.startsWith("https://")) {
    url = "wss://" + url.slice(8);
  } else if (url.startsWith("http://")) {
    url = "ws://" + url.slice(7);
  }

  // 5. Ensure scheme is present
  if (!url.startsWith("ws://") && !url.startsWith("wss://")) {
    const isHttps = typeof window !== "undefined" ? window.location.protocol === "https:" : true;
    url = (isHttps ? "wss://" : "ws://") + url;
  }

  // 6. Ensure trailing /ws endpoint
  url = url.replace(/\/+$/, "");
  if (!url.endsWith("/ws")) {
    url = `${url}/ws`;
  }

  return url;
}

class WebSocketClient {
  private socket: WebSocket | null = null;
  private listeners: Set<WebSocketListener> = new Set();
  private reconnectTimeout: any = null;
  private pingInterval: any = null;
  public isConnected: boolean = false;
  private statusListeners: Set<(connected: boolean) => void> = new Set();

  public connect() {
    if (typeof window === "undefined") return;
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const currentUrl = resolveWebSocketUrl();
    if (!currentUrl) {
      this.notifyStatus(false);
      return;
    }

    try {
      console.log(`[ResQ Web WS] Connecting to: ${currentUrl}`);
      this.socket = new WebSocket(currentUrl);

      this.socket.onopen = () => {
        console.log(`[ResQ Web WS] Connected successfully to ${currentUrl}`);
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
              console.error("[ResQ Web WS] Error in message listener:", err);
            }
          });
        } catch {
          // Plaintext message (e.g. "pong")
        }
      };

      this.socket.onclose = (event) => {
        console.log(`[ResQ Web WS] Disconnected (code: ${event.code}, reason: "${event.reason || 'normal'}"). Scheduling reconnect...`);
        this.isConnected = false;
        this.notifyStatus(false);
        this.stopPing();
        this.scheduleReconnect();
      };

      this.socket.onerror = (err) => {
        console.warn(`[ResQ Web WS] Error event on ${currentUrl}:`, err);
        if (this.socket) {
          try {
            this.socket.close();
          } catch {}
        }
      };
    } catch (err) {
      console.error(`[ResQ Web WS] Initialization exception for ${currentUrl}:`, err);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) return;
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, 3000);
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

