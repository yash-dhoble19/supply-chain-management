import { useEffect, useRef, useCallback } from "react";
import { procurementService } from "../services/procurementService";
import { inventoryService } from "../services/inventoryService";
import type { PurchaseOrder } from "../types/procurement.types";
import type { InventoryItem } from "../types/inventory.types";

interface POItem {
  id?: number | string;
  sku?: string;
  product_name?: string;
  name?: string;
  quantity_ordered?: number;
  quantity_delivered?: number;
  unit_price?: number;
}

/**
 * Hook to sync Procurement "Delivered" status to Inventory
 * When a PO status becomes "Delivered", auto-create inventory entry if not exists
 */
export const useProcurementInventorySync = (
  onSync?: (message: string) => void,
  autoRefreshIntervalMs: number = 30000, // Poll every 30 seconds
) => {
  const lastSyncedIdsRef = useRef<Set<string>>(new Set());
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const syncDeliveredPOs = useCallback(async () => {
    try {
      // Fetch all POs with Delivered status
      const purchaseOrders = (await procurementService.getPurchaseOrders({ status: "Delivered" })) as any[];

      if (!Array.isArray(purchaseOrders)) return;

      for (const po of purchaseOrders) {
        const poId = String(po.id);
        // Skip if already synced
        if (lastSyncedIdsRef.current.has(poId)) continue;

        // Extract product info from PO items
        const poItems = (po.items || po.line_items || []) as POItem[];
        if (Array.isArray(poItems) && poItems.length > 0) {
          for (const item of poItems) {
            try {
              // Auto-create inventory entry with delivered quantity
              const inventoryPayload = {
                sku: item.sku || `SYNC-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                name: item.product_name || item.name || "Unknown Product",
                category: "Procurement Sync",
                stage: "WAREHOUSE",
                current_stock: item.quantity_delivered || item.quantity_ordered || 0,
                safety_stock_level: Math.ceil(((item.quantity_delivered || item.quantity_ordered || 0) * 0.1)),
                optimal_stock_level: Math.ceil(((item.quantity_delivered || item.quantity_ordered || 0) * 0.2)),
                unit_price: item.unit_price || 0,
              };

              await inventoryService.createProduct(inventoryPayload);
              onSync?.(
                `Synced: ${item.product_name || item.name} (${item.quantity_delivered || item.quantity_ordered} units) from PO`,
              );

              lastSyncedIdsRef.current.add(poId);
            } catch (err) {
              // Handle duplicate SKU or other creation errors gracefully
              if (err instanceof Error && err.message.includes("SKU exists")) {
                lastSyncedIdsRef.current.add(poId);
              } else {
                console.warn(`Could not sync item from PO ${poId}:`, err);
              }
            }
          }
        }
      }
    } catch (err) {
      console.error("Procurement inventory sync failed:", err);
    }
  }, [onSync]);

  // Auto-sync on mount and periodically
  useEffect(() => {
    syncDeliveredPOs();
    intervalRef.current = setInterval(syncDeliveredPOs, autoRefreshIntervalMs);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [syncDeliveredPOs, autoRefreshIntervalMs]);

  return { syncDeliveredPOs };
};
