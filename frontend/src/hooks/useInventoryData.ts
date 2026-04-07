import { useCallback, useEffect, useMemo, useState } from "react";
import { inventoryService } from "../services/inventoryService";
import type { InventorySummary, InventoryItem, InventoryActivityItem } from "../types/inventory.types";

interface InventoryState {
  items: InventoryItem[];
  summary: InventorySummary | null;
  activity: InventoryActivityItem[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  page: number;
  limit: number;
  total: number;
}

const initialState: InventoryState = {
  items: [],
  summary: null,
  activity: [],
  isLoading: true,
  error: null,
  lastUpdated: null,
  page: 1,
  limit: 20,
  total: 0,
};

const INVENTORY_CACHE_TTL_MS = 30_000;
const inventoryCache = new Map<
  string,
  {
    data: Omit<InventoryState, "isLoading" | "error">;
    cachedAt: number;
  }
>();

// Export cache clearing function for mutations
export const clearInventoryCache = () => inventoryCache.clear();

export function useInventoryData() {
  const [state, setState] = useState<InventoryState>(initialState);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const cacheKey = `${state.page}-${state.limit}`;
    const cachedEntry = inventoryCache.get(cacheKey);
    const cached = cachedEntry && Date.now() - cachedEntry.cachedAt < INVENTORY_CACHE_TTL_MS ? cachedEntry : null;

    if (cached) {
      setState({
        ...cached.data,
        isLoading: false,
        error: null,
      });
    }

    async function fetchData() {
      setState((prev) => ({ ...prev, isLoading: !cached, error: null }));
      try {
        const response = await inventoryService.getBootstrap(
          { page: state.page, limit: state.limit },
          controller.signal,
        );

        const nextState = {
          items: response.inventory.items,
          summary: response.summary,
          activity: response.activity,
          lastUpdated: new Date(),
          page: response.inventory.page,
          limit: response.inventory.limit,
          total: response.inventory.total,
        };

        inventoryCache.set(cacheKey, {
          data: nextState,
          cachedAt: Date.now(),
        });

        setState({
          ...nextState,
          isLoading: false,
          error: null,
        });
      } catch (err) {
        if (controller.signal.aborted) return;
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : "Failed to load inventory",
        }));
      }
    }

    void fetchData();

    return () => {
      controller.abort();
    };
  }, [reloadToken, state.page, state.limit]);

  const setPage = useCallback((page: number) => setState((prev) => ({ ...prev, page })), []);
  const setLimit = useCallback((limit: number) => setState((prev) => ({ ...prev, limit })), []);
  const refetch = useCallback(() => setReloadToken((prev) => prev + 1), []);

  return useMemo(
    () => ({
      ...state,
      setPage,
      setLimit,
      refetch,
    }),
    [refetch, setLimit, setPage, state],
  );
}
