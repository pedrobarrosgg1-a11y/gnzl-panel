import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api, isAbortError, toApiError, type ApiError } from "../services/api";
import type { SystemConfig } from "../types/api";

type ConfigStatus = "loading" | "ready" | "error";

interface SystemConfigValue {
  status: ConfigStatus;
  config: SystemConfig | null;
  error: ApiError | null;
  reload: () => void;
}

const SystemConfigContext = createContext<SystemConfigValue | null>(null);

export function SystemConfigProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<ConfigStatus>("loading");
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    setError(null);

    api
      .getConfig({ signal: controller.signal })
      .then((data) => {
        setConfig(data);
        setStatus("ready");
      })
      .catch((cause: unknown) => {
        if (isAbortError(cause)) {
          return;
        }
        setConfig(null);
        setError(toApiError(cause));
        setStatus("error");
      });

    return () => controller.abort();
  }, [reloadToken]);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  const value = useMemo(
    () => ({ status, config, error, reload }),
    [status, config, error, reload],
  );

  return (
    <SystemConfigContext.Provider value={value}>
      {children}
    </SystemConfigContext.Provider>
  );
}

export function useSystemConfig(): SystemConfigValue {
  const value = useContext(SystemConfigContext);
  if (!value) {
    throw new Error("useSystemConfig precisa estar dentro de SystemConfigProvider.");
  }
  return value;
}
