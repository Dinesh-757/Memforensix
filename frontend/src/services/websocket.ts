export interface ProgressMessage {
  type: "connected" | "progress" | "ping";
  analysis_id?: string;
  status?: string;
  progress?: number;
  stage?: string;
  message?: string;
}

export class AnalysisSocket {
  private ws: WebSocket | null = null;
  private analysisId: string;
  private onMessage: (msg: ProgressMessage) => void;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private closedByClient = false;

  constructor(analysisId: string, onMessage: (msg: ProgressMessage) => void) {
    this.analysisId = analysisId;
    this.onMessage = onMessage;
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/api/v1/ws/analysis/${this.analysisId}`;
    this.ws = new WebSocket(url);

    this.ws.onmessage = (event) => {
      try {
        const data: ProgressMessage = JSON.parse(event.data);
        this.onMessage(data);
      } catch {
        // ignore malformed frames
      }
    };

    this.ws.onclose = () => {
      if (!this.closedByClient && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts += 1;
        setTimeout(() => this.connect(), 1500 * this.reconnectAttempts);
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  close() {
    this.closedByClient = true;
    this.ws?.close();
  }
}
