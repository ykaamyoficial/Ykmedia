import { useCallback, useEffect, useRef, useState } from "react";

import { fetchEvolutionLicense, startEvolutionLicenseRegistration } from "@/features/settings/api";

/** Enquanto o cadastro esta aberto no navegador, verificamos a licenca. */
const POLL_MS = 3000;
/** O token do servidor de licencas vale 30 min; paramos um pouco antes. */
const MAX_WAIT_MS = 25 * 60 * 1000;

export type ActivationPhase = "idle" | "loading" | "waiting" | "activated" | "error";

export type LicenseActivation = {
  phase: ActivationPhase;
  registerUrl: string | null;
  errorMessage: string | null;
  start: () => void;
  stop: () => void;
};

function isActive(status: string | undefined): boolean {
  return status === "ATIVA" || status === "NAO_EXIGIDA";
}

/**
 * Conduz a ativacao da licenca gratuita da Evolution.
 *
 * O cadastro acontece no navegador e termina com um redirecionamento que ativa
 * a instancia. Sem esta deteccao o app continuava mostrando "Pendente" ate
 * alguem lembrar de clicar em "Verificar" — quem instala numa igreja nao tem
 * por que saber disso.
 */
export function useEvolutionLicenseActivation(onActivated?: () => void): LicenseActivation {
  const [phase, setPhase] = useState<ActivationPhase>("idle");
  const [registerUrl, setRegisterUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const activeRef = useRef(false);
  const timerRef = useRef<number | null>(null);
  const activatedRef = useRef(onActivated);

  useEffect(() => {
    activatedRef.current = onActivated;
  }, [onActivated]);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    activeRef.current = false;
    clearTimer();
    setPhase("idle");
    setRegisterUrl(null);
    setErrorMessage(null);
  }, [clearTimer]);

  const start = useCallback(() => {
    clearTimer();
    activeRef.current = true;
    setPhase("loading");
    setErrorMessage(null);

    void startEvolutionLicenseRegistration()
      .then((state) => {
        if (!activeRef.current) {
          return;
        }

        if (isActive(state.status)) {
          activeRef.current = false;
          setPhase("activated");
          activatedRef.current?.();
          return;
        }

        if (!state.register_url) {
          activeRef.current = false;
          setPhase("error");
          setErrorMessage(state.message || "Não foi possível obter o endereço de cadastro.");
          return;
        }

        setRegisterUrl(state.register_url);
        setPhase("waiting");

        const startedAt = Date.now();
        timerRef.current = window.setInterval(() => {
          if (!activeRef.current) {
            return;
          }

          if (Date.now() - startedAt > MAX_WAIT_MS) {
            activeRef.current = false;
            clearTimer();
            setPhase("error");
            setErrorMessage("O cadastro expirou. Clique em Ativar licença para gerar outro.");
            return;
          }

          void fetchEvolutionLicense()
            .then((current) => {
              if (activeRef.current && isActive(current.status)) {
                activeRef.current = false;
                clearTimer();
                setRegisterUrl(null);
                setPhase("activated");
                activatedRef.current?.();
              }
            })
            .catch(() => {
              /* falha pontual nao interrompe a espera */
            });
        }, POLL_MS);
      })
      .catch(() => {
        if (!activeRef.current) {
          return;
        }
        activeRef.current = false;
        setPhase("error");
        setErrorMessage("Não foi possível falar com o backend.");
      });
  }, [clearTimer]);

  useEffect(() => {
    return () => {
      activeRef.current = false;
      clearTimer();
    };
  }, [clearTimer]);

  return { phase, registerUrl, errorMessage, start, stop };
}
