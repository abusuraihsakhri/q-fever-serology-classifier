// Clinical serologic interpretation. Keep thresholds in sync with serology_interpreter.py.
export function parseTiter(value, optional = false) {
  if (value === null || value === undefined || String(value).trim() === "") {
    if (optional) return null;
    throw new Error("Both phase I and phase II IgG titers are required.");
  }
  const raw = String(value).trim().replace(/^1:/, "");
  if (!/^\d+$/.test(raw)) throw new Error("Enter a denominator such as 256 or 1:256; qualitative titers are not supported.");
  const n = Number(raw);
  if (!Number.isSafeInteger(n) || n < 0 || n > 16777216) throw new Error("Enter a valid nonnegative whole-number titer (up to 16777216).");
  return n;
}

export function classify(phaseIInput, phaseIIInput, priorInput = "", hasFocus = false) {
  const phaseI = parseTiter(phaseIInput);
  const phaseII = parseTiter(phaseIIInput);
  const prior = parseTiter(priorInput, true);
  const fourfold = prior !== null && prior > 0 && phaseII >= prior * 4;
  const highPhaseI = phaseI >= 1024;
  const supportivePhaseII = phaseII >= 128;
  if (highPhaseI && hasFocus) return {status: "persistent_pattern_with_focus", label: "Persistent Q fever: serology plus reported focus", guidance: "A compatible persistent focus and high phase I IgG fulfill key diagnostic elements; obtain specialist confirmation of the focus and full clinical assessment.", fourfold};
  if (highPhaseI) return {status: "investigate_persistent_focus", label: "High phase I IgG: assess for persistent focus", guidance: "Evaluate for endocarditis, vascular infection, or another persistent focus. High phase I IgG alone does not confirm chronic Q fever.", fourfold};
  if (fourfold) return {status: "acute_seroconversion_pattern", label: "Acute Q fever seroconversion pattern", guidance: "A >=4-fold phase II IgG rise on paired IFA supports acute Q fever in a clinically compatible patient. Verify timing and laboratory comparability.", fourfold};
  if (supportivePhaseII) return {status: "single_sample_supportive", label: "Single-sample supportive serology", guidance: "A single phase II IgG titer cannot establish acute infection; correlate clinically and obtain paired sera when indicated.", fourfold};
  return {status: "insufficient_serologic_evidence", label: "No definitive serologic pattern from supplied values", guidance: "Early negative serology does not exclude Q fever; consider PCR in the early illness window and convalescent IFA 3–6 weeks later.", fourfold};
}

const form = typeof document === "undefined" ? null : document.getElementById("serology-form");
if (form) form.addEventListener("submit", event => {
  event.preventDefault();
  const resultEl = document.getElementById("result");
  const statusEl = document.getElementById("result-status");
  const detailsEl = document.getElementById("result-details");
  try {
    const result = classify(
      document.getElementById("phase-i").value,
      document.getElementById("phase-ii").value,
      document.getElementById("prior-phase-ii").value,
      document.getElementById("persistent-focus").checked
    );
    statusEl.textContent = result.label;
    detailsEl.textContent = result.guidance + (result.fourfold ? " A >=4-fold phase II IgG rise was demonstrated." : "");
    resultEl.hidden = false;
    document.getElementById("error").textContent = "";
  } catch (error) {
    resultEl.hidden = true;
    document.getElementById("error").textContent = error.message;
  }
});
