"use client";

import React from "react";
import { X, FileText, Bookmark } from "lucide-react";

interface EvidenceRef {
  document_id: string;
  filename: string;
  page_number: number;
  excerpt: string;
}

interface EvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: EvidenceRef[];
  title?: string;
}

export default function EvidenceModal({
  isOpen,
  onClose,
  evidence,
  title = "Source Grounding & Page References"
}: EvidenceModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="relative w-full max-w-2xl bg-[#0D1410] rounded-2xl shadow-2xl border border-[#26382D] overflow-hidden flex flex-col max-h-[85vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[#26382D] flex items-center justify-between bg-[#142019]">
          <div className="flex items-center gap-2 text-[#F9F9F9] font-bold text-base">
            <Bookmark className="w-4 h-4 text-[#24EACE]" />
            <span className="truncate max-w-md">{title}</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#A7B8AE] hover:text-[#F9F9F9] hover:bg-[#0D1410] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          {evidence && evidence.length > 0 ? (
            evidence.map((item, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-[#26382D] bg-[#142019] space-y-2.5"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-[#A7B8AE]">
                  <span className="flex items-center gap-1.5 text-[#F9F9F9]">
                    <FileText className="w-3.5 h-3.5 text-[#24EACE]" />
                    {item.filename || "Study Material"}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-[#0D2418] text-[#A3FF70] font-bold border border-[#1C4D34]">
                    Page {item.page_number}
                  </span>
                </div>

                <div className="text-sm font-sans leading-relaxed text-[#F9F9F9] bg-[#060807] p-3.5 rounded-lg border border-[#26382D]">
                  &ldquo;{item.excerpt}&rdquo;
                </div>

                <div className="text-[11px] text-[#6C8074] flex items-center justify-between">
                  <span>Document ID: {item.document_id ? item.document_id.slice(0, 8) : "local"}</span>
                  <span className="text-[#A3FF70] font-medium">Verifiable syllabus grounding</span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-[#A7B8AE] italic text-center py-8">
              No direct document excerpt attached to this question.
            </p>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-[#26382D] bg-[#142019] flex items-center justify-between text-xs text-[#A7B8AE]">
          <span>ExamLoop Source Verification Protocol</span>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-[#24EACE] hover:bg-[#A3FF70] text-[#060807] rounded-xl font-bold transition shadow-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
