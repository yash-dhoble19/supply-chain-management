import React, { useState, useEffect } from "react";
import { Search, History, MessageSquare, AlertCircle, FileText, CheckCircle2, ChevronDown, ListFilter, Play } from "lucide-react";
import type { AppPage } from "../types/app.types";

interface AiToolsProps {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

// Interfaces aligned with FastAPI backend output
interface Supplier {
  supplier_id: number;
  name: string;
  company_name: string;
  contact_email: string;
  contact_person: string;
  location: string;
  product_name: string;
  product_category: string;
  unit_price: number;
  currency: string;
  average_delivery_days: number;
  reliability_percent: number;
  ai_score: number;
  responsiveness: string;
  source: string;
  phone: string;
}

interface SupplierSearchResult {
  session_id: number;
  session_code: string;
  product_name: string;
  total_found: number;
  suppliers: Supplier[];
}

interface InteractionDetail {
  interaction_id: number;
  session_id: number;
  supplier_name: string;
  supplier_email: string;
  product_name: string;
  quantity: number;
  status: string;
  sent_at: string;
  has_quote: boolean;
  extracted_quote?: any;
}

export function AiTools({ activePage, onNavigate }: AiToolsProps) {
  const [activeTab, setActiveTab] = useState<"finder" | "communication">("finder");

  // Finder State
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SupplierSearchResult | null>(null);
  const [selectedSuppliers, setSelectedSuppliers] = useState<number[]>([]);
  const [inspectedSupplier, setInspectedSupplier] = useState<Supplier | null>(null);
  const [isSending, setIsSending] = useState(false);

  // Comm State
  const [interactions, setInteractions] = useState<InteractionDetail[]>([]);
  const [isLoadingComms, setIsLoadingComms] = useState(false);
  const [viewQuoteData, setViewQuoteData] = useState<any>(null);

  // --- Search Logic ---
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery) return;

    setIsSearching(true);
    try {
      const BASE_URL = "http://localhost:8000";
      const res = await fetch(`${BASE_URL}/api/ai-tools/supplier-search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_name: searchQuery,
          sources: ["internal"],
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSearchResults(data);
        setSelectedSuppliers([]); // reset selection
        setInspectedSupplier(null);
      } else {
        console.error("Search failed. Check backend.");
      }
    } catch (err) {
      console.error("Error reaching backend.", err);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleSupplier = (supplierId: number) => {
    setSelectedSuppliers((prev) =>
      prev.includes(supplierId)
        ? prev.filter((id) => id !== supplierId)
        : [...prev, supplierId]
    );
  };

  const handleSendInquiry = async () => {
    if (!searchResults || selectedSuppliers.length === 0) return;
    
    const quantity = "1000";
    
    setIsSending(true);
    try {
      const BASE_URL = "http://localhost:8000";
      const res = await fetch(`${BASE_URL}/api/ai-tools/send-inquiry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: searchResults.session_id,
          supplier_ids: selectedSuppliers,
          product_name: searchResults.product_name,
          quantity: parseInt(quantity, 10) || 1000,
        }),
      });

      if (res.ok) {
        setActiveTab("communication"); // Auto-switch to tracking tab
      } else {
        const err = await res.json();
        console.error(`Failed to trigger: ${err.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Error triggering inquiry.", err);
    } finally {
      setIsSending(false);
    }
  };

  // --- Communications Logic ---
  const fetchInteractions = async () => {
    setIsLoadingComms(true);
    try {
      const BASE_URL = "http://localhost:8000";
      const res = await fetch(`${BASE_URL}/api/ai-tools/communication/interactions?page_size=50`);
      if (res.ok) {
        const data = await res.json();
        setInteractions(data.items);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingComms(false);
    }
  };

  useEffect(() => {
    if (activeTab === "communication") {
      fetchInteractions();
      // Optional: Polling every 15s to auto-update replies
      const interval = setInterval(fetchInteractions, 15000);
      return () => clearInterval(interval);
    }
  }, [activeTab]);


  // --- Render Helpers ---
  const renderStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    switch (s) {
      case "inquiry_pending":
      case "sent":
        return <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700"><Play className="h-3 w-3" /> Sending</span>;
      case "follow_up_sent":
        return <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2 py-1 text-xs font-semibold text-orange-700"><MessageSquare className="h-3 w-3" /> Follow-up</span>;
      case "reply_received":
        return <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-700"><CheckCircle2 className="h-3 w-3" /> Replied</span>;
      case "escalated":
        return <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-1 text-xs font-semibold text-red-700"><AlertCircle className="h-3 w-3" /> Escalated</span>;
      default:
        return <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-700">{status}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-background text-on-surface">
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-on-surface">AI Procurement Assistant</h1>
            <p className="mt-2 text-on-surface-variant">
              Autonomously source, contact, and negotiate with suppliers using intelligent agents.
            </p>
          </div>
        </div>

        {/* --- Tabs --- */}
        <div className="mb-6 flex gap-4 border-b border-outline-variant pb-px">
          <button
            onClick={() => setActiveTab("finder")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2 font-medium ${
              activeTab === "finder"
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:border-outline-variant hover:text-on-surface"
            }`}
          >
            <Search className="h-4 w-4" />
            Supplier Finder
          </button>
          <button
            onClick={() => setActiveTab("communication")}
            className={`flex items-center gap-2 border-b-2 px-4 py-2 font-medium ${
              activeTab === "communication"
                ? "border-primary text-primary"
                : "border-transparent text-on-surface-variant hover:border-outline-variant hover:text-on-surface"
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            Communication Hub
          </button>
        </div>

        {/* --- Tab Content: Finder --- */}
        {activeTab === "finder" && (
          <div className="space-y-6">
            {/* Search Card */}
            <div className="rounded-3xl border border-outline-variant bg-surface-container-lowest p-6 shadow-sm">
              <form onSubmit={handleSearch} className="flex items-center gap-4">
                <div className="relative flex-1">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Search className="h-5 w-5 text-on-surface-variant" />
                  </div>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="block w-full rounded-xl border-0 py-3 pl-10 pr-3 text-on-surface ring-1 ring-inset ring-outline-variant focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm sm:leading-6"
                    placeholder="Describe the product you need (e.g. 'Steel Pipes 10cm' or 'Copper Wire')..."
                  />
                </div>
                <button
                  type="submit"
                  disabled={isSearching}
                  className="rounded-xl bg-primary px-6 py-3 font-semibold text-on-primary shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
                >
                  {isSearching ? "Searching..." : "Find Suppliers"}
                </button>
              </form>
            </div>

            {/* Results Target */}
            {searchResults && (
              <div className="flex flex-col lg:flex-row gap-6 items-start">
                <div className="flex-1 w-full rounded-3xl border border-outline-variant bg-surface-container-lowest shadow-sm overflow-hidden">
                  <div className="border-b border-outline-variant bg-surface-container-low px-6 py-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-on-surface">Top Matches for "{searchResults.product_name}"</h3>
                      <p className="text-sm text-on-surface-variant">Found {searchResults.total_found} verified suppliers</p>
                    </div>
                    <button
                      onClick={handleSendInquiry}
                      disabled={isSending || selectedSuppliers.length === 0}
                      className="rounded-xl bg-secondary px-6 py-2 text-sm font-semibold text-on-secondary shadow-sm hover:bg-secondary/90 disabled:opacity-50"
                    >
                      {isSending ? "Triggering AI Workflow..." : `Launch AI Campaign (${selectedSuppliers.length})`}
                    </button>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-outline-variant">
                      <thead className="bg-surface-container-lowest">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-on-surface-variant">Select</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-on-surface-variant">Supplier</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-on-surface-variant">Est. Price</th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-on-surface-variant">AI Match Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-outline-variant bg-surface-container-lowest">
                        {searchResults.suppliers.map((supplier) => (
                          <tr 
                            key={supplier.supplier_id} 
                            className={`hover:bg-surface-container-low/50 cursor-pointer ${inspectedSupplier?.supplier_id === supplier.supplier_id ? "bg-surface-container-low" : ""}`}
                            onClick={() => setInspectedSupplier(supplier)}
                          >
                            <td className="whitespace-nowrap px-6 py-4" onClick={(e) => e.stopPropagation()}>
                              <input
                                type="checkbox"
                                className="h-4 w-4 rounded border-outline-variant text-primary focus:ring-primary cursor-pointer"
                                checked={selectedSuppliers.includes(supplier.supplier_id)}
                                onChange={() => toggleSupplier(supplier.supplier_id)}
                              />
                            </td>
                            <td className="whitespace-nowrap px-6 py-4">
                              <div className="flex items-center">
                                <div className="h-10 w-10 flex-shrink-0 flex items-center justify-center rounded-full bg-primary-container text-on-primary-container font-semibold">
                                  {supplier.name.charAt(0)}
                                </div>
                                <div className="ml-4">
                                  <div className="font-medium text-on-surface">{supplier.company_name}</div>
                                  <div className="text-sm text-on-surface-variant">{supplier.location}</div>
                                </div>
                              </div>
                            </td>
                            <td className="whitespace-nowrap px-6 py-4 text-sm text-on-surface-variant">
                              {supplier.unit_price ? `${supplier.currency} ${supplier.unit_price}` : "Needs Quote"}
                            </td>
                            <td className="whitespace-nowrap px-6 py-4">
                              <div className="flex items-center gap-2">
                                <div className="h-2 w-24 rounded-full bg-surface-container-highest overflow-hidden">
                                  <div 
                                    className="h-full bg-primary" 
                                    style={{ width: `${Math.min(100, Math.max(0, supplier.ai_score))}%` }}
                                  />
                                </div>
                                <span className="text-sm font-medium text-on-surface">{supplier.ai_score.toFixed(0)}</span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {inspectedSupplier && (
                  <div className="w-full lg:w-80 shrink-0 rounded-3xl border border-outline-variant bg-surface-container-lowest p-6 shadow-sm flex flex-col gap-4 sticky top-6">
                    <div className="flex justify-between items-start">
                      <div className="h-12 w-12 flex items-center justify-center rounded-full bg-primary-container text-on-primary-container text-lg font-bold">
                        {inspectedSupplier.name.charAt(0)}
                      </div>
                      <button onClick={() => setInspectedSupplier(null)} className="text-on-surface-variant hover:text-on-surface font-black">✕</button>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-on-surface">{inspectedSupplier.company_name}</h3>
                      <p className="text-sm font-medium text-primary mt-1">{inspectedSupplier.source?.replace("ZENROWS_", "") || "EXTERNAL"}</p>
                    </div>
                    
                    <div className="rounded-xl bg-primary-container/30 p-4 border border-primary-container">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-primary font-bold">✨ AI Insight & Match Score</span>
                      </div>
                      <p className="text-sm text-on-surface-variant leading-relaxed">
                        This supplier achieved an <strong className="text-on-surface">{inspectedSupplier.ai_score.toFixed(0)}/100</strong> AI Match Score. 
                        The engine determined this is a {inspectedSupplier.ai_score >= 85 ? "highly optimal" : "viable"} choice by weighing their 
                        <strong className="text-on-surface"> {inspectedSupplier.reliability_percent || 85}% reliability index</strong> against their fast
                        <strong className="text-on-surface"> {inspectedSupplier.average_delivery_days}-day</strong> fulfillment window.
                      </p>
                      
                      <div className="text-sm text-on-surface-variant leading-relaxed mt-3 p-3 bg-white border border-outline-variant rounded-lg">
                        <strong className="text-primary block mb-1">Why the AI recommends this:</strong> 
                        Because successful procurement requires strict adherence to lead times, the AI prioritized this supplier's low historical fulfillment delays. Combined with their standing in the {inspectedSupplier.source?.replace("ZENROWS_", "") || "B2B"} market, they are categorized as a low-risk, high-efficiency partner for sourcing <span className="font-semibold">{searchResults.product_name || "this product"}</span>.
                      </div>
                    </div>
                    
                    <div className="space-y-3 mt-2 border-t border-outline-variant pt-4">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Location</p>
                        <p className="text-sm text-on-surface mt-1">{inspectedSupplier.location}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Email</p>
                        <p className="text-sm text-on-surface mt-1">{inspectedSupplier.contact_email}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Phone #</p>
                        <p className="text-sm text-on-surface mt-1">{inspectedSupplier.phone || "Not provided"}</p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Contact Person</p>
                        <p className="text-sm text-on-surface mt-1">{inspectedSupplier.contact_person}</p>
                      </div>
                      <div>
                         <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Delivery Speed</p>
                         <p className="text-sm text-on-surface mt-1">{inspectedSupplier.average_delivery_days} Business Days</p>
                      </div>
                    </div>
                    
                    <button 
                      onClick={() => toggleSupplier(inspectedSupplier.supplier_id)}
                      className={`mt-4 w-full rounded-xl border px-4 py-2 font-semibold transition-colors ${
                        selectedSuppliers.includes(inspectedSupplier.supplier_id) 
                        ? "border-error text-error hover:bg-error/10" 
                        : "border-primary text-primary hover:bg-primary/10"
                      }`}
                    >
                      {selectedSuppliers.includes(inspectedSupplier.supplier_id) ? "Remove from Campaign" : "Add to Campaign"}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* --- Tab Content: Communication Hub --- */}
        {activeTab === "communication" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-on-surface">Active Sourcing Campaigns</h2>
              <button 
                onClick={fetchInteractions}
                className="text-sm font-medium text-primary hover:text-primary/80"
              >
                Refresh Data
              </button>
            </div>

            {isLoadingComms ? (
              <div className="flex justify-center p-12">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
              </div>
            ) : interactions.length === 0 ? (
              <div className="rounded-3xl border border-outline-variant bg-surface-container-lowest p-12 text-center">
                <MessageSquare className="mx-auto h-12 w-12 text-on-surface-variant opacity-50" />
                <h3 className="mt-4 text-lg font-medium text-on-surface">No active interactions</h3>
                <p className="mt-2 text-on-surface-variant">Start a new campaign from the Supplier Finder to see tracked emails here.</p>
              </div>
            ) : (
              <div className="rounded-3xl border border-outline-variant bg-surface-container-lowest shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-outline-variant">
                    <thead className="bg-surface-container-low">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-on-surface-variant">Target Supplier</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-on-surface-variant">Product Context</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-on-surface-variant">Automated Journey Status</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-on-surface-variant">Results</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-outline-variant bg-surface-container-lowest">
                      {interactions.map((ix) => (
                        <tr key={ix.interaction_id} className="hover:bg-surface-container-low/50 transition-colors">
                          <td className="whitespace-nowrap px-6 py-4">
                            <div className="font-medium text-on-surface">{ix.supplier_name}</div>
                            <div className="text-sm text-on-surface-variant">{ix.supplier_email || "Contact sync pending"}</div>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4">
                            <div className="text-sm font-medium text-on-surface">{ix.product_name}</div>
                            <div className="text-xs text-on-surface-variant">Qty: {ix.quantity}</div>
                          </td>
                          <td className="whitespace-nowrap px-6 py-4">
                            {renderStatusBadge(ix.status)}
                            {ix.sent_at && (
                              <div className="mt-1 text-xs text-on-surface-variant">
                                Started: {new Date(ix.sent_at).toLocaleDateString()}
                              </div>
                            )}
                          </td>
                          <td className="whitespace-nowrap px-6 py-4">
                            {ix.has_quote ? (
                              <button 
                                onClick={() => setViewQuoteData(ix.extracted_quote)}
                                className="inline-flex items-center gap-1 rounded bg-tertiary-container px-2 py-1 text-xs font-semibold text-on-tertiary-container hover:bg-tertiary-container/80 transition-colors">
                                <FileText className="h-3 w-3" /> View AI Extracted Quote
                              </button>
                            ) : ix.status === "reply_received" ? (
                              <span className="text-sm text-amber-600 font-medium italic">Requires manual review</span>
                            ) : (
                              <span className="text-sm text-on-surface-variant italic">Waiting for reply...</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* --- Quote Detail Modal --- */}
        {viewQuoteData && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-lg rounded-3xl bg-surface p-6 shadow-xl border border-outline-variant">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-on-surface flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  AI Extracted Quote
                </h3>
                <button onClick={() => setViewQuoteData(null)} className="text-on-surface-variant hover:text-on-surface">✕</button>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-4">
                    <p className="text-xs font-medium text-on-surface-variant uppercase tracking-wider mb-1">Unit Price</p>
                    <p className="text-lg font-bold text-primary">{viewQuoteData.pricePerUnit ? `$${viewQuoteData.pricePerUnit}` : "Needs check"}</p>
                  </div>
                  <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-4">
                    <p className="text-xs font-medium text-on-surface-variant uppercase tracking-wider mb-1">MOQ</p>
                    <p className="text-lg font-bold text-on-surface">{viewQuoteData.moq || "N/A"}</p>
                  </div>
                  <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-4">
                    <p className="text-xs font-medium text-on-surface-variant uppercase tracking-wider mb-1">Delivery</p>
                    <p className="text-lg font-bold text-on-surface">{viewQuoteData.deliveryDate || "N/A"}</p>
                  </div>
                  <div className="rounded-xl border border-outline-variant bg-surface-container-lowest p-4">
                    <p className="text-xs font-medium text-on-surface-variant uppercase tracking-wider mb-1">Terms</p>
                    <p className="text-sm font-semibold text-on-surface">{viewQuoteData.paymentTerms || "N/A"}</p>
                  </div>
                </div>
                {viewQuoteData.contactDetails && (
                  <div className="rounded-xl border border-outline-variant bg-surface-container p-4">
                    <p className="text-xs font-medium text-on-surface-variant uppercase tracking-wider mb-1">Contact Note</p>
                    <p className="text-sm text-on-surface">{viewQuoteData.contactDetails}</p>
                  </div>
                )}
              </div>
              <div className="mt-6 flex justify-end">
                <button 
                  onClick={() => setViewQuoteData(null)}
                  className="rounded-xl bg-primary px-6 py-2 text-sm font-semibold text-on-primary hover:bg-primary/90"
                >
                  Confirm & Close
                </button>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

// anything
