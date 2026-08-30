import { useCallback, useEffect, useRef, useState } from "react";

import { connectEvolutionSession, fetchEvolutionSession } from "@/features/settings/api";

/** O QR do WhatsApp expira em cerca de 40s; renovamos antes disso. */
const QR_LIFETIME_SECONDS = 40;
const REFRESH_AT_SECONDS = 5;
/** Enquanto o QR esta na tela, verificamos a conexao com frequencia. */
const STATE_POLL_MS = 3000;

export type PairingPhase = "idle" | "loading" | "waiting" | "connected" | "error";

export type WhatsAppPairing = {
  phase: PairingPhase;
  qrcodeBase64: string | null;
  secondsLeft: number;
  errorMessage: string | null;
  start: () => void;
  stop: () => void;
};

function isConnected(state: string | undefined): boolean {
  return (state ?? "").toLowerCase() === "open";
}

/**
 * Conduz o pareamento do WhatsApp do inicio ao fim.
 *
 * Antes o QR era pedido uma vez e ficava parado na tela: como ele expira em
 * poucos segundos, quem abria o WhatsApp para escanear quase sempre encontrava
 * um codigo morto, sem nenhum aviso. Aqui o codigo se renova sozinho, mostra
 * quanto tempo resta e detecta a conexao assim que ela acontece.
 */
export function useWhatsAppPairing(): WhatsAppPairing {
  const [phase, setPhase] = useState<PairingPhase>("idle");
  const [qrcodeBase64, setQrcodeBase64] = useState<string | null>(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const activeRef = useRef(false);
  const timersRef = useRef<number[]>([]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((id) => window.clearInterval(id));
    timersRef.current = [];
  }, []);

  const stop = useCallback(() => {
    activeRef.current = false;
    clearTimers();
    setPhase("idle");
    setQrcodeBase64(null);
    setSecondsLeft(0);
    setErrorMessage(null);
  }, [clearTimers]);

  const requestQrcode = useCallback(async () => {
    try {
      const session = await connectEvolutionSession();

      if (!activeRef.current) {
        return;
      }

      if (isConnected(session.state)) {
        clearTimers();
        activeRef.current = false;
        setPhase("connected");
        setQrcodeBase64(null);
        return;
      }

      if (!session.qrcode_base64) {
        setPhase("error");
        setErrorMessage(session.message || "A Evolution não devolveu o QR Code.");
        activeRef.current = false;
        clearTimers();
        return;
      }

      setQrcodeBase64(session.qrcode_base64);
      setSecondsLeft(QR_LIFETIME_SECONDS);
      setPhase("waiting");
      setErrorMessage(null);
    } catch {
      if (!activeRef.current) {
        return;
      }
      setPhase("error");
      setErrorMessage("Não foi possível falar com o backend.");
      activeRef.current = false;
      clearTimers();
    }
  }, [clearTimers]);

  const start = useCallback(() => {
    clearTimers();
    activeRef.current = true;
    setPhase("loading");
    setErrorMessage(null);
    void requestQrcode();

    // Conta regressiva; ao chegar perto do fim, pede um QR novo.
    const countdown = window.setInterval(() => {
      setSecondsLeft((current) => {
        if (!activeRef.current) {
          return current;
        }
        if (current <= REFRESH_AT_SECONDS) {
          void requestQrcode();
          return QR_LIFETIME_SECONDS;
        }
        return current - 1;
      });
    }, 1000);

    // Detecta a conexao sem depender de o usuario clicar em "Verificar".
    const poll = window.setInterval(() => {
      if (!activeRef.current) {
        return;
      }
      void fetchEvolutionSession()
        .then((session) => {
          if (activeRef.current && isConnected(session.state)) {
            activeRef.current = false;
            clearTimers();
            setPhase("connected");
            setQrcodeBase64(null);
            setSecondsLeft(0);
          }
        })
        .catch(() => {
          /* falha pontual de rede nao interrompe o pareamento */
        });
    }, STATE_POLL_MS);

    timersRef.current = [countdown, poll];
  }, [clearTimers, requestQrcode]);

  useEffect(() => {
    return () => {
      activeRef.current = false;
      clearTimers();
    };
  }, [clearTimers]);

  return { phase, qrcodeBase64, secondsLeft, errorMessage, start, stop };
}
