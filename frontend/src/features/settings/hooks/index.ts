export {
  useConnectEvolutionSession,
  useDisconnectEvolutionSession,
  useEvolutionLicense,
  useEvolutionSession,
  usePrepareSystem,
  useRunDiagnostics,
  useSaveSettings,
  useSettings,
  useStartEvolutionLicenseRegistration,
} from "@/features/settings/hooks/useSettings";
export { useWhatsAppPairing, type PairingPhase, type WhatsAppPairing } from "@/features/settings/hooks/useWhatsAppPairing";
export {
  useEvolutionLicenseActivation,
  type ActivationPhase,
  type LicenseActivation,
} from "@/features/settings/hooks/useEvolutionLicenseActivation";
