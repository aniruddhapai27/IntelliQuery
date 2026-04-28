import { useState, useRef, useEffect, useCallback } from "react";
import { aiAPI, formatApiError } from "../../../utils/api";

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

/**
 * ExportActions — renders "Export CSV" and "Email Results" buttons
 * beneath the results / visualization of each AI response.
 *
 * Props:
 *   results   — the row data (array of objects)
 *   columns   — optional column list
 *   chartData — optional Plotly JSON figure ({ data, layout })
 */
export default function ExportActions({ results, columns, chartData }) {
  /* ------------------------------------------------------------------ */
  /*  State                                                              */
  /* ------------------------------------------------------------------ */
  const [csvLoading, setCsvLoading] = useState(false);
  const [csvDone, setCsvDone] = useState(false);

  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailInput, setEmailInput] = useState("");
  const [recipients, setRecipients] = useState([]);
  const [emailError, setEmailError] = useState("");
  const [emailSubject, setEmailSubject] = useState(
    "IntelliQuery — Your Query Results",
  );
  const [emailMessage, setEmailMessage] = useState("");
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailSuccess, setEmailSuccess] = useState(false);

  const modalRef = useRef(null);
  const emailInputRef = useRef(null);

  /* ------------------------------------------------------------------ */
  /*  Reset CSV tick after 3 seconds                                     */
  /* ------------------------------------------------------------------ */
  useEffect(() => {
    if (!csvDone) return;
    const t = setTimeout(() => setCsvDone(false), 3000);
    return () => clearTimeout(t);
  }, [csvDone]);

  /* ------------------------------------------------------------------ */
  /*  Close modal on outside click                                       */
  /* ------------------------------------------------------------------ */
  useEffect(() => {
    if (!showEmailModal) return;
    const handler = (e) => {
      if (modalRef.current && !modalRef.current.contains(e.target)) {
        setShowEmailModal(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [showEmailModal]);

  /* Focus email input when modal opens */
  useEffect(() => {
    if (showEmailModal) emailInputRef.current?.focus();
  }, [showEmailModal]);

  /* ------------------------------------------------------------------ */
  /*  CSV Export                                                          */
  /* ------------------------------------------------------------------ */
  const handleExportCSV = useCallback(async () => {
    if (!results?.length) return;
    setCsvLoading(true);
    try {
      const res = await aiAPI.exportCSV({ results, columns });
      const blob = new Blob([res.data], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "query_results.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setCsvDone(true);
    } catch (err) {
      console.error("CSV export failed:", err);
      alert(
        formatApiError(err.response?.data) ||
          "Failed to export CSV. Please try again.",
      );
    } finally {
      setCsvLoading(false);
    }
  }, [results, columns]);

  /* ------------------------------------------------------------------ */
  /*  Email — recipient chip management                                   */
  /* ------------------------------------------------------------------ */
  const addRecipient = useCallback(
    (raw) => {
      const email = raw.trim().toLowerCase();
      if (!email) return;
      if (!EMAIL_REGEX.test(email)) {
        setEmailError(`"${email}" is not a valid email address.`);
        return;
      }
      if (recipients.includes(email)) {
        setEmailError(`"${email}" is already added.`);
        return;
      }
      if (recipients.length >= 20) {
        setEmailError("Maximum 20 recipients allowed.");
        return;
      }
      setRecipients((prev) => [...prev, email]);
      setEmailInput("");
      setEmailError("");
    },
    [recipients],
  );

  const removeRecipient = useCallback((email) => {
    setRecipients((prev) => prev.filter((r) => r !== email));
    setEmailError("");
  }, []);

  const handleEmailKeyDown = useCallback(
    (e) => {
      if (e.key === "Enter" || e.key === "," || e.key === " ") {
        e.preventDefault();
        addRecipient(emailInput);
      }
      if (
        e.key === "Backspace" &&
        emailInput === "" &&
        recipients.length > 0
      ) {
        removeRecipient(recipients[recipients.length - 1]);
      }
    },
    [emailInput, addRecipient, removeRecipient, recipients],
  );

  /* ------------------------------------------------------------------ */
  /*  Email — send                                                        */
  /* ------------------------------------------------------------------ */
  const handleSendEmail = useCallback(async () => {
    // Add any leftover text in the input field
    if (emailInput.trim()) {
      const email = emailInput.trim().toLowerCase();
      if (!EMAIL_REGEX.test(email)) {
        setEmailError(`"${email}" is not a valid email address.`);
        return;
      }
      if (!recipients.includes(email)) {
        setRecipients((prev) => [...prev, email]);
      }
      setEmailInput("");
    }

    const finalRecipients =
      emailInput.trim() && EMAIL_REGEX.test(emailInput.trim().toLowerCase())
        ? [...recipients, emailInput.trim().toLowerCase()]
        : recipients;

    if (finalRecipients.length === 0) {
      setEmailError("Please add at least one recipient.");
      return;
    }

    setEmailLoading(true);
    setEmailError("");
    setEmailSuccess(false);

    try {
      await aiAPI.emailResults({
        recipients: finalRecipients,
        results,
        columns: columns || null,
        chart_data: chartData || null,
        subject: emailSubject || undefined,
        message: emailMessage || undefined,
      });
      setEmailSuccess(true);
      // Auto-close after 2s
      setTimeout(() => {
        setShowEmailModal(false);
        setEmailSuccess(false);
        setRecipients([]);
        setEmailInput("");
        setEmailSubject("IntelliQuery — Your Query Results");
        setEmailMessage("");
      }, 2000);
    } catch (err) {
      console.error("Email send failed:", err);
      setEmailError(
        formatApiError(err.response?.data) ||
          "Failed to send email. Please try again.",
      );
    } finally {
      setEmailLoading(false);
    }
  }, [
    emailInput,
    recipients,
    results,
    columns,
    chartData,
    emailSubject,
    emailMessage,
  ]);

  /* ------------------------------------------------------------------ */
  /*  Open email modal (reset state)                                      */
  /* ------------------------------------------------------------------ */
  const openEmailModal = useCallback(() => {
    setEmailError("");
    setEmailSuccess(false);
    setShowEmailModal(true);
  }, []);

  if (!results?.length) return null;

  /* ------------------------------------------------------------------ */
  /*  Render                                                              */
  /* ------------------------------------------------------------------ */
  return (
    <>
      {/* Action Buttons */}
      <div className="mt-4 flex items-center gap-3">
        {/* Export CSV */}
        <button
          onClick={handleExportCSV}
          disabled={csvLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                     bg-gray-800 border border-gray-700 text-gray-300
                     hover:bg-gray-700 hover:border-yellow-600/50 hover:text-yellow-400
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all duration-200"
        >
          {csvLoading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-transparent" />
          ) : csvDone ? (
            <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          )}
          {csvDone ? "Downloaded" : "Export CSV"}
        </button>

        {/* Email Results */}
        <button
          onClick={openEmailModal}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                     bg-gray-800 border border-gray-700 text-gray-300
                     hover:bg-gray-700 hover:border-yellow-600/50 hover:text-yellow-400
                     transition-all duration-200"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Email Results
        </button>
      </div>

      {/* Email Modal Overlay */}
      {showEmailModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div
            ref={modalRef}
            className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl shadow-yellow-600/10 w-full max-w-lg mx-4 animate-fade-in"
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <h3 className="text-lg font-semibold text-white">
                  Email Results
                </h3>
              </div>
              <button
                onClick={() => setShowEmailModal(false)}
                className="text-gray-500 hover:text-gray-300 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="px-6 py-5 space-y-4 max-h-[70vh] overflow-y-auto">
              {/* Success State */}
              {emailSuccess && (
                <div className="flex flex-col items-center justify-center py-8 space-y-3">
                  <div className="w-14 h-14 rounded-full bg-green-500/20 flex items-center justify-center">
                    <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="text-green-400 font-medium">Email sent successfully!</p>
                  <p className="text-gray-500 text-sm">
                    Sent to {recipients.length} recipient{recipients.length !== 1 ? "s" : ""}
                  </p>
                </div>
              )}

              {!emailSuccess && (
                <>
                  {/* Recipients */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1.5">
                      Recipients <span className="text-red-400">*</span>
                    </label>
                    <div className="bg-gray-800 border border-gray-700 rounded-lg p-2 focus-within:ring-2 focus-within:ring-yellow-600 focus-within:border-transparent transition-all">
                      {/* Chips */}
                      <div className="flex flex-wrap gap-1.5 mb-1">
                        {recipients.map((email) => (
                          <span
                            key={email}
                            className="inline-flex items-center gap-1 bg-yellow-600/20 text-yellow-400 border border-yellow-600/40 rounded-full px-2.5 py-0.5 text-xs"
                          >
                            {email}
                            <button
                              onClick={() => removeRecipient(email)}
                              className="hover:text-red-400 transition-colors ml-0.5"
                              type="button"
                            >
                              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          </span>
                        ))}
                      </div>
                      {/* Input */}
                      <input
                        ref={emailInputRef}
                        type="text"
                        value={emailInput}
                        onChange={(e) => {
                          setEmailInput(e.target.value);
                          setEmailError("");
                        }}
                        onKeyDown={handleEmailKeyDown}
                        onBlur={() => {
                          if (emailInput.trim()) addRecipient(emailInput);
                        }}
                        placeholder={
                          recipients.length === 0
                            ? "Type email and press Enter"
                            : "Add another..."
                        }
                        className="w-full bg-transparent text-white text-sm placeholder-gray-600 outline-none"
                      />
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      Press Enter, comma, or space to add. Backspace to remove last.
                    </p>
                  </div>

                  {/* Subject */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1.5">
                      Subject
                    </label>
                    <input
                      type="text"
                      value={emailSubject}
                      onChange={(e) => setEmailSubject(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                    />
                  </div>

                  {/* Message */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1.5">
                      Message{" "}
                      <span className="text-gray-600 font-normal">(optional)</span>
                    </label>
                    <textarea
                      value={emailMessage}
                      onChange={(e) => setEmailMessage(e.target.value)}
                      rows={3}
                      placeholder="Add a personal message..."
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-600 resize-none focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                    />
                  </div>

                  {/* Attachment Preview */}
                  <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3 space-y-2">
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Attachments
                    </p>
                    <div className="flex items-center gap-2 text-sm text-gray-300">
                      <svg className="w-4 h-4 text-green-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>query_results.csv</span>
                      <span className="text-gray-600 text-xs">
                        ({results.length} rows)
                      </span>
                    </div>
                    {chartData && (
                      <div className="flex items-center gap-2 text-sm text-gray-300">
                        <svg className="w-4 h-4 text-blue-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <span>chart.png</span>
                        <span className="text-gray-600 text-xs">(visualization)</span>
                      </div>
                    )}
                  </div>

                  {/* Error */}
                  {emailError && (
                    <div className="bg-red-500/10 border border-red-500/40 text-red-400 px-3 py-2 rounded-lg text-sm flex items-start gap-2">
                      <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {emailError}
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Modal Footer */}
            {!emailSuccess && (
              <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-800">
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendEmail}
                  disabled={emailLoading || (recipients.length === 0 && !emailInput.trim())}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold
                             bg-gradient-to-r from-yellow-600 to-yellow-500 text-black
                             hover:from-yellow-500 hover:to-yellow-400
                             shadow-lg shadow-yellow-600/30 hover:shadow-yellow-500/50
                             disabled:opacity-50 disabled:cursor-not-allowed
                             transition-all duration-200"
                >
                  {emailLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-black border-t-transparent" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                      </svg>
                      Send Email
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
