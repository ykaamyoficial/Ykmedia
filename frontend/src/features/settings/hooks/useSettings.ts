import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  connectEvolutionSession,
  disconnectEvolutionSession,
  fetchEvolutionSession,
  fetchSettings,
  prepareSystem,
  runDiagnostics,
  saveSettings,
} from "@/features/settings/api";
import { type AppSettings } from "@/features/settings/types";
import { queryKeys } from "@/shared/query";

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings.detail,
    queryFn: fetchSettings,
    staleTime: 10000,
  });
}

export function useSaveSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: AppSettings) => saveSettings(settings),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.settings.detail });
    },
  });
}

export function useEvolutionSession() {
  return useQuery({
    queryKey: queryKeys.settings.evolution,
    queryFn: fetchEvolutionSession,
    staleTime: 10000,
  });
}

export function useConnectEvolutionSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: connectEvolutionSession,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.settings.evolution }),
        queryClient.invalidateQueries({ queryKey: queryKeys.settings.detail }),
      ]);
    },
  });
}

export function useDisconnectEvolutionSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disconnectEvolutionSession,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.settings.evolution }),
        queryClient.invalidateQueries({ queryKey: queryKeys.settings.detail }),
      ]);
    },
  });
}

export function usePrepareSystem() {
  return useMutation({ mutationFn: prepareSystem });
}

export function useRunDiagnostics() {
  return useMutation({ mutationFn: runDiagnostics });
}
