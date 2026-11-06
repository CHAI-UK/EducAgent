const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const BRIEF_FIELD_LIMIT = 2000;
const CONTEXT_LIMIT = 16000;
const REQUEST_BYTE_LIMIT = 32768;

function framingRequest(payload) {
  if (payload.context.length > CONTEXT_LIMIT) {
    throw new Error("Your Brief and reasoning exceed the 16,000-character context limit. Shorten them before sending. Your draft is unchanged.");
  }
  const history = [...payload.history];
  const encode = () => JSON.stringify({...payload, history});
  let body = encode();
  while (new TextEncoder().encode(body).length > REQUEST_BYTE_LIMIT && history.length) {
    history.shift();
    body = encode();
  }
  if (new TextEncoder().encode(body).length > REQUEST_BYTE_LIMIT) {
    throw new Error("Your Brief and message exceed the 32 KB request limit. Shorten them before sending. Your draft is unchanged.");
  }
  return {body, omittedHistory: payload.history.length - history.length};
}

const effectFields = [
  ["decision", "Intended decision or purpose"],
  ["exposure", "Exposure or intervention"],
  ["comparator", "Comparator"],
  ["outcome", "Outcome"],
  ["population", "Population"],
  ["time", "Time horizon"],
  ["assumptions", "Assumptions & uncertainty"],
];
const shiftFields = [
  ["prediction-target", "Prediction or generation target and intended use"],
  ["candidate-predictors", "Candidate predictors and measurement timing"],
  ["training-environment", "Training environment"],
  ["deployment-environment", "Expected deployment environment"],
  ["shift-sources", "Suspected shifted variable or mechanism"],
  ["predictor-roles", "How predictors may relate to the target"],
  ["deployment-constraints", "Deployment data and adaptation constraints"],
  ["shift-uncertainty", "Assumptions & uncertainty"],
];
const mediationFields = [
  ["mediation-decision", "Intended decision or scientific purpose"],
  ["mediation-exposure", "Exposure or intervention"],
  ["mediator", "Proposed mediator"],
  ["mediation-outcome", "Outcome"],
  ["mediation-population", "Population"],
  ["mediation-effect", "Target effect"],
  ["mediation-time", "Time ordering"],
  ["mediation-uncertainty", "Assumptions & uncertainty"],
];
const descriptiveFields = [
  ["descriptive-purpose", "Purpose"],
  ["descriptive-population", "Population or cohort"],
  ["descriptive-measure", "Measure"],
  ["descriptive-denominator", "Denominator"],
  ["descriptive-strata", "Breakdowns or strata"],
  ["descriptive-time", "Time window"],
  ["descriptive-limitations", "Data source & limitations"],
];
const additionalTasks = {
  "discovery": {
    "label": "Causal structure discovery",
    "hint": "Which variables cause which others?",
    "fields": [
      [
        "discovery-purpose",
        "Scientific purpose"
      ],
      [
        "discovery-variables",
        "Candidate variables and measurement timing"
      ],
      [
        "discovery-data",
        "Observations, interventions and sampling"
      ],
      [
        "discovery-knowledge",
        "Known ordering and structural constraints"
      ],
      [
        "discovery-uncertainty",
        "Latent variables, measurement and uncertainty"
      ]
    ],
    "summary": "Causal discovery can help investigate candidate directed relationships. Observational associations alone do not uniquely determine a causal graph; interventions, temporal knowledge and assumptions need specialist review."
  },
  "policy": {
    "label": "Action or policy choice",
    "hint": "Which action should be assigned to whom, under constraints?",
    "fields": [
      [
        "policy-purpose",
        "Decision and target population"
      ],
      [
        "policy-actions",
        "Available actions and current policy"
      ],
      [
        "policy-objective",
        "Outcome, utility and time horizon"
      ],
      [
        "policy-information",
        "Information available when choosing"
      ],
      [
        "policy-constraints",
        "Budget, capacity and other constraints"
      ],
      [
        "policy-evidence",
        "Data and evidence about action effects"
      ],
      [
        "policy-uncertainty",
        "Assumptions and uncertainty"
      ]
    ],
    "summary": "Causal effects may support comparisons of action policies, not just prediction of high-risk individuals. A specialist should assess treatment-effect evidence, objectives and constraints before recommending any policy."
  },
  "counterfactual": {
    "label": "Individual counterfactual",
    "hint": "For this same observed case, what if something had been different?",
    "fields": [
      [
        "cf-purpose",
        "Purpose and factual case"
      ],
      [
        "cf-observed",
        "Observed state and outcome"
      ],
      [
        "cf-intervention",
        "Hypothetical intervention and contrast"
      ],
      [
        "cf-target",
        "Counterfactual outcome of interest"
      ],
      [
        "cf-model",
        "Structural knowledge and case-preserving assumptions"
      ],
      [
        "cf-uncertainty",
        "Evidence, identifiability and uncertainty"
      ]
    ],
    "summary": "A structural causal model may formalise what would differ for the same observed case under an alternative intervention. This requires stronger case-level assumptions than predicting another observation; image translation alone is not evidence of a valid counterfactual."
  },
  "prediction": {
    "label": "Prediction without a shift question",
    "hint": "What outcome can we predict using information available now?",
    "fields": [
      [
        "prediction-purpose",
        "Intended use and population"
      ],
      [
        "prediction-outcome",
        "Target and prediction horizon"
      ],
      [
        "prediction-inputs",
        "Inputs available at prediction time"
      ],
      [
        "prediction-data",
        "Training and evaluation data"
      ],
      [
        "prediction-evaluation",
        "Success criteria and validation plan"
      ],
      [
        "prediction-uncertainty",
        "Leakage, missingness and uncertainty"
      ]
    ],
    "summary": "Ordinary outcome prediction does not itself require causal identification. Causal framing becomes relevant if the goal changes to interventions, counterfactuals or robustness under changing mechanisms."
  }
};
const taskFields = {
  ...Object.fromEntries(Object.entries(additionalTasks).map(([id, spec]) => [id, spec.fields])),
  effect: effectFields,
  shift: shiftFields,
  mediation: mediationFields,
  descriptive: descriptiveFields,
};
const multilineFields = new Set([
  ...Object.values(additionalTasks).flatMap((spec) => spec.fields.map(([id]) => id)),
  "problem",
  "assumptions",
  "candidate-predictors",
  "shift-sources",
  "predictor-roles",
  "deployment-constraints",
  "shift-uncertainty",
  "mediation-uncertainty",
  "descriptive-limitations",
]);
const initialValues = new Map(
  [["problem"], ...Object.values(taskFields).flat()].map(([id]) => [id, $(`#${id}`).value]),
);
// Literature-inspired hypothetical stories, not reproductions or empirical findings.
const literatureExamples = {
  "effect": {
    "title": "Oregon Medicaid experiment",
    "citation": "Baicker et al. (2013), New England Journal of Medicine",
    "url": "https://pubmed.ncbi.nlm.nih.gov/23635051/",
    "task": "effect",
    "problem": "Oregon used a lottery to select low-income adults from a waiting list for the opportunity to apply for Medicaid. We want to estimate how Medicaid coverage affects depression screening outcomes about two years later, compared with not having coverage. How should we frame this effect question while distinguishing random lottery selection from actual insurance enrolment?"
  },
  "shift": {
    "title": "Prostate MRI across centres",
    "citation": "Ouyang et al. (2023), IEEE Transactions on Medical Imaging",
    "url": "https://pubmed.ncbi.nlm.nih.gov/36417741/",
    "task": "shift",
    "problem": "We train a prostate MRI segmentation model using labelled scans from one centre and want it to remain reliable on scans from other centres with different acquisition processes. Can causality-inspired methods help the model avoid relying on centre-specific image appearance? How should we specify the source and deployment environments, suspected shifts and evaluation needs? We do not yet know whether target-centre data will be available before deployment."
  },
  "mediation": {
    "title": "How pain education and exercise help",
    "citation": "Murillo et al. (2023), Pain",
    "url": "https://pubmed.ncbi.nlm.nih.gov/37289577/",
    "task": "mediation",
    "problem": "In a primary-care trial for chronic spinal pain, participants receive either pain neuroscience education combined with exercise or standard physiotherapy. We want to investigate whether reduced fear of movement after treatment mediates an improvement in disability at six-month follow-up. How should we define this indirect effect and its assumptions, given that treatment is randomised but fear of movement is not? Other potential mediators may also be involved."
  },
  "descriptive": {
    "title": "Population obesity trends",
    "citation": "Hales et al. (2018), JAMA",
    "url": "https://jamanetwork.com/journals/jama/fullarticle/2676543",
    "task": "descriptive",
    "problem": "Using repeated NHANES surveys from 2007-2008 through 2015-2016, we want to describe obesity and severe obesity prevalence among US adults aged 20 and older, including breakdowns by sex and age and changes over survey cycles. How should we specify the population, BMI-based measures, survey weights and reporting periods? We are describing population trends, not estimating the effect of an intervention."
  },
  "ehr_predict": {
    "title": "Predicting readmission from EHRs",
    "citation": "Rajkomar et al. (2018), npj Digital Medicine",
    "url": "https://www.nature.com/articles/s41746-018-0029-1",
    "task": "prediction",
    "problem": "We want to use electronic health records available at hospital discharge to predict whether a patient will have an unplanned readmission within 30 days. Our immediate goal is to evaluate predictive accuracy in our hospital data, not to estimate a treatment effect or claim robustness at a new hospital. How should we define the target, allowable inputs and validation plan?"
  },
  "adni_discovery": {
    "title": "Alzheimer's biomarker relationships",
    "citation": "Challenges and Opportunities with Causal Discovery Algorithms: Application to Alzheimer's Pathophysiology (2020), Scientific Reports",
    "url": "https://www.nature.com/articles/s41598-020-59669-x",
    "task": "discovery",
    "problem": "We have ADNI observational data on Alzheimer's disease biomarkers, including amyloid beta, phosphorylated tau, FDG-PET, APOE genotype and clinical or cognitive measurements. We want to investigate candidate causal directions among these variables, rather than only predict a diagnosis. How should we frame a causal structure discovery study, combining the data with biological knowledge while accounting for unmeasured factors and uncertainty in the graph?"
  },
  "depression_policy": {
    "title": "Sequential depression treatment",
    "citation": "Pineau et al. (2007), Drug and Alcohol Dependence",
    "url": "https://pubmed.ncbi.nlm.nih.gov/17320311/",
    "task": "policy",
    "problem": "Using data from the STAR*D study, we want to investigate a sequence of treatment-selection rules for people with depression. At each treatment stage, the rule would use information already available about the patient's response to earlier treatment to choose among eligible next options, aiming to improve subsequent depression outcomes. How should we specify the decision stages, available actions, patient history and objective? This is a research question about treatment policies, not a request for advice for an individual patient."
  },
  "brain_cf": {
    "title": "The same brain, different ventricle volume",
    "citation": "Pawlowski et al. (2020), NeurIPS",
    "url": "https://arxiv.org/abs/2006.06485",
    "task": "counterfactual",
    "problem": "For one observed brain MRI, we want to ask what the image would look like under a hypothetical intervention that changes ventricle volume in a structural causal model while preserving the same subject's inferred background factors. How should we specify the factual scan, the intervention, the counterfactual image target and the model assumptions? The generated image would be a model-dependent hypothetical, not an observed alternative outcome or a validated clinical prediction."
  }
};
Object.entries(NirvanaWorkedExamples).forEach(([id, worked]) => Object.assign(literatureExamples[id], worked));
const exampleProblems = {
  ...Object.fromEntries(Object.entries(literatureExamples).map(([id, example]) => [id, example.problem])),
  ctpa: `I am working on CT Pulmonary Angiography (CTPA) exams. More specifically, I want to synthesize the non-contrast CTPA from the contrast CTPA. Within my data population there people with very different demographics that could play a role in the exam. Additionally, this model should work with exams that come from different company scanners (Siemens, Phillips, Canon, GE etc.).

I want to know whether causality can make this model robust to distribution shifts.`,
};
const directRouteTasks = new Set(["other"]);

let task = null;
let selectedExample = null;
let revision = 0;
let confirmedRevision = null;
let handoffSnapshot = "";
let pendingChat = null;
let draftState = "idle";

function setDraftState(state, message = "") {
  draftState = state;
  $("#draft-status").textContent = message;
  $("#retry-draft").classList.toggle("hidden", state !== "error");
}
let categorising = false;
let awaitingTaskReview = false;
let framingReviewed = false;
let problemConcepts = [];
let helpSequence = 0;
const taskDrafts = new Map();
let fieldsProblem = "";
const chat = [];
let proposals = [];
// One finite pass per explicit start. Pause/resume never resets consumed items.
let briefCheck = null;
let nextReview = null;

function syncReviewFocus() {
  if (!briefCheck || briefCheck.paused || proposals.length) return;
  const fields = taskFields[task] || [];
  const target = nextReview && fields.findIndex(([id]) => id === nextReview.field_id);
  if (nextReview && target >= 0 && !briefCheck.resolved?.[nextReview.field_id]) {
    briefCheck.index = target;
    briefCheck.question = nextReview.question;
  } else if (briefCheck.resolved?.[fields[briefCheck.index]?.[0]]) {
    const remaining = fields.findIndex(([id]) => !briefCheck.resolved?.[id]);
    briefCheck.index = remaining < 0 ? fields.length : remaining;
    briefCheck.question = "";
  }
  nextReview = null;
  briefCheck.skipped = Object.values(briefCheck.resolved || {}).filter(item => item.skipped).length;
}
function renderBriefCheck() {
  const fields = taskFields[task] || [];
  $("#brief-check").classList.toggle("hidden", !fields.length);
  const current = fields[briefCheck?.index ?? 0];
  const finished = briefCheck && !current;
  const locked = Boolean(pendingChat) || proposals.length > 0;
  $("#check-question").textContent = !briefCheck
    ? "Start a Brief review."
    : finished
    ? `Review pass finished. Items left for later: ${briefCheck.skipped}.`
    : briefCheck.paused
    ? "Review paused. You can keep chatting or resume the review when ready."
    : proposals.length
    ? "Review the proposed edits above first. Your next question will appear here after Accept/Reject."
    : `Item ${briefCheck.index + 1}/${fields.length}: ${current[1]}\n${briefCheck.question || "Is this entry accurate and clear? Reply below to refine it, confirm it, or leave it for later."}`;
  $("#check-help").textContent = current ? NirvanaGuidance.help[current[0]] : "No further items in this pass.";
  for (const id of ["check-confirm", "check-skip", "check-pause"]) {
    $("#" + id).disabled = !briefCheck || finished || locked || (briefCheck.paused && id !== "check-pause");
  }
  $("#check-pause").textContent = briefCheck?.paused ? "Resume review" : "Pause review";
  $("#check-start").disabled = !fields.length || locked || Boolean(briefCheck && !finished);
}
function advanceBriefCheck(skip = false) {
  if (!briefCheck || briefCheck.paused || pendingChat || proposals.length || briefCheck.index >= (taskFields[task] || []).length) return;
  (briefCheck.resolved ||= {})[taskFields[task][briefCheck.index][0]] = {skipped: skip};
  briefCheck.question = "";
  nextReview = null;
  syncReviewFocus();
  renderBriefCheck();
}
$("#check-start").addEventListener("click", () => {
  if ($("#check-start").disabled) return;
  briefCheck = { index: 0, skipped: 0, paused: false };
  nextReview = null;
  renderBriefCheck();
});
$("#check-confirm").addEventListener("click", () => advanceBriefCheck());
$("#check-skip").addEventListener("click", () => advanceBriefCheck(true));
$("#check-pause").addEventListener("click", () => {
  if ($("#check-pause").disabled) return;
  briefCheck.paused = !briefCheck.paused;
  if (!briefCheck.paused) syncReviewFocus();
  renderBriefCheck();
});

function renderProposals() {
  const root = $("#brief-proposals");
  root.replaceChildren();
  root.classList.toggle("hidden", proposals.length === 0);
  proposals.forEach((proposal) => {
    const card = document.createElement("section");
    const heading = document.createElement("strong");
    heading.textContent = proposal.label;
    const before = document.createElement("p");
    before.className = "diff-before";
    before.textContent = `Before: ${proposal.before || "Unknown / not provided"}`;
    const after = document.createElement("textarea");
    after.className = "diff-after";
    after.value = proposal.after;
    after.maxLength = BRIEF_FIELD_LIMIT;
    after.setAttribute("aria-describedby", "brief-field-limit");
    after.setAttribute("aria-label", `Edit proposed change to ${proposal.label}`);
    after.addEventListener("input", () => { proposal.after = after.value; });
    card.append(heading, before, after);
    for (const accept of [true, false]) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "quiet";
      button.textContent = accept ? "Accept" : "Reject";
      button.setAttribute("aria-label", `${button.textContent} change to ${proposal.label}`);
      button.addEventListener("click", () => {
        if (accept) {
          $(`#${proposal.id}`).value = proposal.after;
          briefChanged(true);
          renderBrief();
        }
        const decision = {
          role: "user",
          text: `${accept ? "Accepted" : "Rejected"} proposed change to ${proposal.label}. Keep this field exactly as this JSON string: ${JSON.stringify(accept ? proposal.after : proposal.before)}`,
          displayText: `${accept ? "Accepted" : "Rejected"} · ${proposal.label}${accept ? "" : " (original kept)"}`,
          rejectedField: accept ? null : proposal.id,
        };
        chat.push(decision);
        if (briefCheck) {
          (briefCheck.resolved ||= {})[proposal.id] = { skipped: !accept };
        }
        proposals = proposals.filter((item) => item !== proposal);
        syncReviewFocus();
        if (!proposals.length && !briefCheck) {
          const missing = (taskFields[task] || []).find(([id]) =>
            !$(`#${id}`).value.trim() && !chat.some((entry) => entry.rejectedField === id));
          if (missing) decision.displayText += `\nStill to clarify: ${missing[1]}. Share what you know, or leave it unknown.`;
        }
        renderProposals();
        renderChat();
        renderBriefCheck();
        $('#agent-form button[type="submit"]').disabled = Boolean(pendingChat) || proposals.length > 0;
        $("#agent-status").textContent = proposals.length ? "Review the remaining changes." : "";
      });
      card.append(button);
    }
    root.append(card);
  });
}

function setCategorising(active) {
  categorising = active;
  $("#task-next").disabled = active || !task;
  $$(".choice").forEach((button) => { button.disabled = active; });
}

// The window is anchored bottom-right, so resize from its opposite corner.
function resizeChat(width, height) {
  const maxWidth = window.innerWidth - 48;
  const maxHeight = window.innerHeight - 112;
  $("#framing-chat").style.width = `${Math.min(maxWidth, Math.max(300, width))}px`;
  $("#framing-chat").style.height = `${Math.min(maxHeight, Math.max(320, height))}px`;
}
let chatDrag = null;
$("#chat-resize").addEventListener("pointerdown", (event) => {
  if (event.button !== 0) return;
  const rect = $("#framing-chat").getBoundingClientRect();
  chatDrag = {x: event.clientX, y: event.clientY, width: rect.width, height: rect.height};
  $("#chat-resize").setPointerCapture(event.pointerId);
  event.preventDefault();
});
$("#chat-resize").addEventListener("pointermove", (event) => {
  if (chatDrag) resizeChat(chatDrag.width + chatDrag.x - event.clientX, chatDrag.height + chatDrag.y - event.clientY);
});
for (const event of ["pointerup", "pointercancel", "lostpointercapture"]) {
  $("#chat-resize").addEventListener(event, () => { chatDrag = null; });
}
$("#chat-resize").addEventListener("keydown", (event) => {
  const delta = {ArrowLeft: [24, 0], ArrowRight: [-24, 0], ArrowUp: [0, 24], ArrowDown: [0, -24]}[event.key];
  if (!delta) return;
  event.preventDefault();
  const rect = $("#framing-chat").getBoundingClientRect();
  resizeChat(rect.width + delta[0], rect.height + delta[1]);
});

function toggleChat(open) {
  $("#framing-chat").classList.toggle("hidden", !open);
  $("#chat-toggle").setAttribute("aria-expanded", String(open));
  if (open) {
    ($("#agent-message").disabled ? $("#chat-close") : $("#agent-message")).focus();
  } else {
    $("#chat-toggle").focus();
  }
}

$("#chat-toggle").addEventListener("click", () => {
  toggleChat($("#chat-toggle").getAttribute("aria-expanded") !== "true");
});
$("#chat-close").addEventListener("click", () => toggleChat(false));
$("#framing-chat").addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    toggleChat(false);
  }
});

function value(id) {
  return $(`#${id}`).value.trim() || "[unknown / not provided]";
}

function taskLabel() {
  if (additionalTasks[task]) return additionalTasks[task].label;
  if (!task) return "Not selected";
  if (task === "effect") return "Effect of an intervention";
  if (task === "shift") return "Robust prediction or generation";
  if (task === "mediation") return "Mechanism or mediation";
  if (task === "descriptive") return "Description or measurement";
  return "Outside the supported demo route";
}

function currentBriefFields() {
  return [["problem", "Research problem"], ...(taskFields[task] || [])];
}

function briefContext(exact = false) {
  if (exact) return [
    briefStatus(), sourceDescription(), `Task class: ${taskLabel()}`,
    `Researcher's reasoning (unverified): ${$("#reasoning-note").value || "Unknown"}`,
    `Research problem: ${$("#problem").value}`,
    briefCheck && !briefCheck.paused && taskFields[task]?.[briefCheck.index]
      ? `Current guided-review item: ${taskFields[task][briefCheck.index][1]}. Interpret the user's reply in this context, unless they ask about another topic.` : "Guided review is not awaiting a specific item.",
    `Current review question: ${briefCheck?.question || "Check the current spec."}`,
    `Already reviewed or deferred field IDs: ${Object.keys(briefCheck?.resolved || {}).join(", ") || "None"}. Do not re-ask these unless explicitly reopened.`,
    "Exact current field values (authoritative worksheet snapshot; preserve unchanged strings):",
    JSON.stringify(Object.fromEntries((taskFields[task] || []).map(([id]) => [id, $(`#${id}`).value]))),
  ].join("\n");
  return [
    briefStatus(),
    sourceDescription(),
    `Task class: ${taskLabel()}`,
    `Researcher's reasoning (unverified): ${$("#reasoning-note").value || "Unknown"}`,
    ...currentBriefFields().map(([id, label]) => `${label}: ${value(id)}`),
  ].join("\n");
}

function sourceDescription() {
  const reference = literatureExamples[selectedExample];
  if (reference) return `Source: worked teaching example based on ${reference.citation}, ${reference.url}. Specs distinguish paper facts from teaching choices; not a replication. See Problem for detailed provenance.`;
  if (selectedExample === "ctpa") return "Source: user-provided CTPA example; AI drafting remains provisional, not verified evidence.";
  return selectedExample
    ? "Source: synthetic example, possibly edited; values and hypotheses are illustrative, not evidence."
    : "Source: user input with optional AI drafting; unverified and subject to researcher review.";
}

function briefStatus() {
  return `Provisional Causal Research Brief. ${confirmedRevision === revision ? "User reviewed this Brief for handoff; this is not evidence verification." : "Draft: not yet reviewed for handoff."}`;
}

function clearChat() {
  nextReview = null;
  setDraftState("idle");
  briefCheck = null;
  proposals = [];
  renderProposals();
  const hadContext = chat.length > 0 || pendingChat;
  pendingChat?.abort();
  pendingChat = null;
  chat.length = 0;
  $("#agent-message").value = "";
  $("#agent-message").disabled = false;
  $('#agent-form button[type="submit"]').disabled = false;
  $("#generate-brief").disabled = false;
  $("#generation-status").textContent = "";
  setCategorising(false);
  $("#agent-status").textContent = hadContext ? "Brief changed; previous conversation cleared." : "";
  renderChat();
  renderBriefCheck();
}

// Every field edit invalidates the same revision and handoff, regardless of editor.
function briefChanged(keepChat = false) {
  revision += 1;
  confirmedRevision = null;
  if (!keepChat) clearChat();
  updateCount();
  renderReview();
  renderRoute();
}

function editField(id, text) {
  if (id === "problem") {
    taskDrafts.clear();
    problemConcepts = [];
    framingReviewed = false;
    $("#reasoning-note").value = "";
  }
  if (id === "problem" && selectedExample) {
    initialValues.forEach((_value, field) => { $(`#${field}`).value = ""; });
    selectedExample = null;
  }
  $(`#${id}`).value = text;
  currentBriefFields().forEach(([field]) => {
    const mirror = $(`[data-bind="${field}"]`);
    if (mirror) mirror.value = $(`#${field}`).value;
  });
  briefChanged();
}

function renderReview() {
  const confirmed = confirmedRevision === revision;
  $("#brief-status").textContent = confirmed ? "CONFIRMED" : "DRAFT";
  $("#confirm-brief").disabled = confirmed || !taskFields[task] || !$("#problem").value.trim();
}

function renderChat() {
  const root = $("#agent-messages");
  root.replaceChildren();
  const messages = chat.length ? chat : [{
    role: "assistant",
    text: "Hi, I'm Nirvana! Tell me about your research question, or ask about a field in your Brief. I can explain causal concepts and help you work out what to clarify next, one question at a time.",
  }];
  const latestAssistant = chat.findLast(entry => entry.role === "assistant");
  messages.forEach((entry) => {
    const {role, text, displayText, reviewQuestion} = entry;
    const message = document.createElement("div");
    if (displayText) {
      message.className = "chat-decision";
      message.textContent = displayText;
      root.append(message);
      return;
    }
    message.className = `agent-message ${role}`;
    const label = document.createElement("strong");
    label.textContent = role === "user" ? "You" : "Nirvana";
    if (role === "assistant") {
      const avatar = document.createElement("img");
      avatar.src = "assets/nirvana-mascot.png";
      avatar.alt = "";
      avatar.className = "message-avatar";
      message.append(avatar);
    }
    const body = document.createElement("div");
    body.className = role === "assistant" ? "chat-markdown" : "chat-plain";
    if (role === "assistant") body.innerHTML = NirvanaMarkdown.render(entry === latestAssistant && reviewQuestion && briefCheck && !briefCheck.paused ? text.slice(0, -reviewQuestion.length).trim() : text);
    else body.textContent = text;
    message.append(label, body);
    root.append(message);
  });
  const scroll = $("#chat-scroll");
  scroll.scrollTop = chat.at(-1)?.role === "assistant" ? (root.children[root.children.length - 1]?.offsetTop || 0) : scroll.scrollHeight;
}

function appendBriefRow(root, label, control) {
  const row = document.createElement("div");
  row.className = "brief-row";
  const term = document.createElement("dt");
  term.textContent = label;
  const detail = document.createElement("dd");
  detail.append(control);
  row.append(term, detail);
  root.append(row);
}

function renderBrief() {
  const root = $("#brief-fields");
  root.replaceChildren();

  const taskValue = document.createElement("p");
  taskValue.className = "brief-value";
  taskValue.textContent = taskLabel();
  appendBriefRow(root, "Task class", taskValue);

  currentBriefFields().forEach(([id, label]) => {
    const control = document.createElement(
      multilineFields.has(id) ? "textarea" : "input",
    );
    control.value = $(`#${id}`).value;
    control.maxLength = BRIEF_FIELD_LIMIT;
    control.setAttribute("aria-describedby", "brief-field-limit");
    control.placeholder = "Unknown / not provided";
    control.dataset.bind = id;
    control.setAttribute("aria-label", label);
    control.addEventListener("input", () => {
      editField(id, control.value);
    });
    appendBriefRow(root, label, control);
    root.children[root.children.length - 1].children[0].append(fieldHelp(id, label));
  });
}

function configureClarification() {
  const clarification = {
    effect: [
      "Clarify the causal contrast",
      "These are researcher-editable working fields. Nothing here is verified evidence.",
    ],
    shift: [
      "Prepare for Domain Generalization Copilot",
      "Capture what you know and mark what remains unknown. Review task fit before choosing a specialist workflow; DG Copilot is a candidate, not an automatic destination.",
    ],
    mediation: [
      "Clarify the proposed mechanism",
      "Record the proposed pathway without treating mediation as established. A specialist must review identification and estimation.",
    ],
    descriptive: [
      "Clarify the descriptive question",
      "Define what will be counted and reported. This question does not require a causal contrast as currently stated.",
    ],
  }[task] || [additionalTasks[task].label, "Review these task-specific specs. Missing facts can remain unknown; the next specialist reviews feasibility and assumptions."];
  $$(".task-fields").forEach((fields) => fields.classList.add("hidden"));
  $(`#${task}-fields`)?.classList.remove("hidden");
  $("#clarify-title").textContent = clarification[0];
}

function fieldHelp(id, label) {
  const detail = document.createElement("span");
  detail.className = "field-help";
  const summary = document.createElement("span");
  summary.className = "help-trigger";
  summary.setAttribute("tabindex", "0");
  summary.textContent = "?";
  summary.setAttribute("aria-label", `Help: ${label}`);
  const explanation = document.createElement("span");
  explanation.className = "help-tooltip";
  explanation.setAttribute("role", "tooltip");
  const tooltipId = `field-help-${++helpSequence}`;
  explanation.setAttribute("id", tooltipId);
  summary.setAttribute("aria-describedby", tooltipId);
  explanation.textContent = NirvanaGuidance.help[id];
  detail.append(summary, explanation);
  const positionHelp = () => {
    detail.classList.remove("dismissed");
    const anchor = summary.getBoundingClientRect();
    explanation.style.left = `${Math.max(12, Math.min(anchor.left, window.innerWidth - explanation.offsetWidth - 12))}px`;
    explanation.style.top = `${Math.max(12, Math.min(anchor.bottom + 3, window.innerHeight - explanation.offsetHeight - 12))}px`;
  };
  detail.addEventListener("mouseenter", positionHelp);
  detail.addEventListener("focusin", positionHelp);
  summary.addEventListener("keydown", event => { if (event.key === "Escape") detail.classList.add("dismissed"); });
  return detail;
}

function renderFraming() {
  const root = $("#framing-lesson");
  root.replaceChildren();
  const lesson = NirvanaGuidance.lessons[task];
  if (!lesson) return;
  for (const concept of problemConcepts.length ? problemConcepts : [{title: lesson.concept, definition: lesson.text, relevance: ""}]) {
    const heading = document.createElement("h3");
    heading.textContent = concept.title;
    const definition = document.createElement("blockquote");
    definition.textContent = `Definition: ${concept.definition}`;
    const relevance = document.createElement("p");
    if (concept.relevance) {
      const label = document.createElement("strong");
      label.textContent = "In your question: ";
      const detail = document.createElement("span");
      detail.textContent = concept.relevance;
      relevance.append(label, detail);
    }
    root.append(heading, definition, relevance);
  }
  const mapping = document.createElement("dl");
  for (const id of lesson.keys) {
    const label = taskFields[task].find(([field]) => field === id)[1];
    const term = document.createElement("dt");
    term.textContent = label;
    const answer = document.createElement("dd");
    answer.textContent = value(id);
    mapping.append(term, answer);
  }
  const question = document.createElement("p");
  question.textContent = lesson.check;
  const source = document.createElement("small");
  source.textContent = `Background reading: Peters, Janzing & Schölkopf, Elements of Causal Inference (2017), §§ ${lesson.sections}. This reference does not verify the AI-selected definitions above.`;
  root.append(mapping, question, source);
}

function go(requestedStep) {
  let nextStep = (categorising || awaitingTaskReview || !task) && requestedStep > 2 ? 2 : requestedStep;
  if (task && nextStep > 2 && directRouteTasks.has(task)) nextStep = 4;
  else if (task && nextStep >= 3 && !framingReviewed) nextStep = 2.5;
  $$(".step-panel").forEach((panel) => {
    panel.classList.toggle("hidden", Number(panel.dataset.panel) !== nextStep);
  });
  $$(".step").forEach((step) => {
    const isCurrent = Number(step.dataset.step) === nextStep;
    step.classList.toggle("active", isCurrent);
    if (isCurrent) step.setAttribute("aria-current", "step");
    else step.removeAttribute("aria-current");
  });
  if (nextStep === 3) {
    configureClarification();
    if (!briefCheck) briefCheck = { index: 0, skipped: 0, paused: false };
    syncReviewFocus();
    renderBriefCheck();
    renderChat();
  }
  if (nextStep === 2.5) renderFraming();
  renderBrief();
  if (nextStep === 4) renderRoute();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function escapeHtml(text) {
  return text.replace(
    /[&<>]/g,
    (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[character],
  );
}

function effectHandoff() {
  return `${briefStatus()}
${sourceDescription()}

Research problem:
${value("problem")}

Intended decision or purpose:
${value("decision")}

User-selected task class:
Effect of an intervention

Causal contrast
- Exposure or intervention: ${value("exposure")}
- Comparator: ${value("comparator")}
- Outcome: ${value("outcome")}
- Population: ${value("population")}
- Time horizon: ${value("time")}

Recorded assumptions and uncertainty (unverified):
${value("assumptions")}

Please recover the intended contrast, flag material missing context or unsupported assumptions, preserve uncertainty, and suggest exactly one bounded next step. Do not invent facts, establish identification, choose a final estimator, run an analysis, or state a causal conclusion.`;
}

function shiftHandoff() {
  return `${briefStatus()}
${sourceDescription()}
Robustness study preparation notes. This is not a causal graph, feasibility assessment, or mitigation recommendation. DG Copilot is one candidate workflow, subject to a task-fit check.

Research problem:
${value("problem")}

Prediction or generation target and intended use:
${value("prediction-target")}

Candidate predictors and measurement timing:
${value("candidate-predictors")}

Training environment:
${value("training-environment")}

Expected deployment environment:
${value("deployment-environment")}

Suspected shifted variable or mechanism:
${value("shift-sources")}

Provisional hypothesis about how predictors relate to the target:
${value("predictor-roles")}

Deployment data and adaptation constraints:
${value("deployment-constraints")}

Recorded assumptions and uncertainty (unverified):
${value("shift-uncertainty")}

First review the prediction or generation target, source/target data, suspected shifts and evaluation plan with an ML/domain specialist or a general-purpose LLM. If DG Copilot fits the agreed problem, manually enter the reviewed details there. There is no automatic import or prompt-paste integration. Nirvana does not pre-fill a graph, choose a robustness method, or guarantee performance.`;
}

function mediationHandoff() {
  return `${briefStatus()}
${sourceDescription()}
Provisional mediation framing for specialist review.

Research problem:
${value("problem")}

Intended purpose:
${value("mediation-decision")}

Proposed mediation framing
- Exposure or intervention: ${value("mediation-exposure")}
- Proposed mediator: ${value("mediator")}
- Outcome: ${value("mediation-outcome")}
- Population: ${value("mediation-population")}
- Target effect: ${value("mediation-effect")}
- Time ordering: ${value("mediation-time")}

Recorded assumptions and uncertainty (unverified):
${value("mediation-uncertainty")}

Please clarify whether the scientific target is a total, direct, or indirect effect; identify material temporal, confounding, and measurement questions; preserve uncertainty; and suggest one bounded next step. Do not treat the proposed mediator as established, claim identification, choose a final estimator, or estimate an effect.`;
}

function descriptiveHandoff() {
  return `${briefStatus()}
${sourceDescription()}
Descriptive analysis brief. No causal contrast is required for the question as currently stated.

Research problem:
${value("problem")}

Descriptive specification
- Purpose: ${value("descriptive-purpose")}
- Population or cohort: ${value("descriptive-population")}
- Measure: ${value("descriptive-measure")}
- Denominator: ${value("descriptive-denominator")}
- Breakdowns or strata: ${value("descriptive-strata")}
- Time window: ${value("descriptive-time")}

Data source and limitations:
${value("descriptive-limitations")}

Please check the operational definitions, denominator, missing-data risks, and reporting breakdowns, then suggest one bounded next step. Do not infer or imply a causal effect.`;
}

function currentHandoff() {
  const handoff = taskHandoff();
  const recommended = recommendDestination();
  const provenance = literatureExamples[selectedExample]?.provenance.map(p => `${p.status} (${p.fields.join(", ")}): ${p.note} ${p.url}`).join("\n") || "";
  return handoff ? `${handoff}\n\nSuggested next workspace: ${recommended.title}\nReason: ${recommended.reason}\nNext: ${recommended.next}${provenance ? `\n\nExample provenance:\n${provenance}` : ""}` : undefined;
}

function taskHandoff() {
  if (task === "other") return `Request for clarification or domain-expert referral\n\nOriginal question:\n${value("problem")}\n\nResearcher's reasoning (unverified):\n${$("#reasoning-note").value || "Not supplied"}\n\nNirvana has not identified a supported research task. The question may be outside its scope or need clarification; this does not establish that causal methods are useful or useless. Please help clarify the intended goal and suggest an appropriate domain expert or next workflow. Do not force the question into a causal task or claim that a causal analysis has been prepared.`;
  if (additionalTasks[task]) return `${briefContext()}\n\n${task === "prediction" ? "Is causality needed here?" : "Where causality can be applied:"}\n${additionalTasks[task].summary}\n\nPrepare a ${taskLabel()} research specification. Review the fields above, distinguish reported facts from assumptions, and identify one useful next step. Do not invent missing facts or claim to have run an analysis. Check scientific assumptions and tool compatibility with an appropriate specialist.`;
  const handoff = {
    effect: effectHandoff,
    shift: shiftHandoff,
    mediation: mediationHandoff,
    descriptive: descriptiveHandoff,
  }[task]?.();
  return handoff ? `${handoff}\n\nResearcher's reasoning (unverified):\n${$("#reasoning-note").value || "Unknown"}` : undefined;
}

function destinationNavigation() {
  const items = NirvanaDestinations[task] || [];
  const recommendation = recommendDestination();
  if (task === "other") return `<section class="tool-navigation"><h3>${escapeHtml(recommendation.title)}</h3><p>${escapeHtml(recommendation.reason)}</p><p>${escapeHtml(recommendation.next)}</p><p class="muted">Only share information approved for the recipient. No content is sent automatically.</p></section>`;
  return `<section class="tool-navigation"><h3>Suggested next step: ${escapeHtml(recommendation.title)}</h3><p>${escapeHtml(recommendation.reason)}</p><p><b>What to do:</b> ${escapeHtml(recommendation.next)}</p><h3>Candidate tools</h3>${items.map((item) => `<details class="route-tool"><summary>${escapeHtml(item.name)}</summary><p>${escapeHtml(item.about)}</p><p><b>Inputs needed:</b> ${escapeHtml(item.inputs)}</p><p><b>Your Brief contributes:</b> ${item.fields.map(id => escapeHtml((taskFields[task] || []).find(([key]) => key === id)?.[1] || id)).join("; ")}.</p><p><b>Next step:</b> ${escapeHtml(item.next)}</p><p><b>Boundary:</b> ${escapeHtml(item.limit)}</p><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Open ${escapeHtml(item.name)} / documentation</a></details>`).join("")}<details class="route-tool"><summary>Methodologist, ChatGPT or Claude (framing help)</summary><p>Copy the current Brief for a human expert or your chosen general-purpose LLM. Ask it to review the requested output, explain unclear concepts, identify missing facts and propose one next step. Keep unknowns explicit and ask a qualified specialist to check any scientific or clinical conclusions.</p><p>Share content manually and only with an approved recipient. Exclude patient identifiers and confidential data. Nirvana does not send, execute or verify anything in these services.</p></details></section>`;
}

function recommendDestination() {
  if (task === "other") return {title: "A relevant domain expert, or ChatGPT / Claude", reason: "Nirvana cannot recommend a task-specific causal tool from this framing. A relevant domain expert can help assess the problem; a general-purpose AI can help clarify your goal and prepare questions for that expert.", next: "Copy the referral note below. Ask what expertise or workflow fits your question, without assuming causality is required. AI suggestions are not a substitute for domain expertise."};
  const fields = taskFields[task] || [];
  const missing = fields.filter(([id]) => !$("#" + id).value.trim() || /^(?:\[?unknown|not (?:provided|reported|specified))/i.test($("#" + id).value.trim()));
  const fallback = {title: "ChatGPT / Claude or a methodologist", reason: "Clarify the problem before running an analysis.", next: "Copy this Brief and ask for a staged analysis plan, missing inputs and assumptions. Check scientific claims and generated code with a qualified reviewer; do not share confidential data without approval."};
  if (!fields.length) return fallback;
  if (missing.length) return {...fallback, reason: `The Brief still leaves ${missing.length} item(s) unresolved, including ${missing.slice(0, 2).map(([, label]) => label).join(" and ")}. A conversational review can clarify these before selecting analysis software.`};
  if (task === "policy" && /sequential|stage|dynamic|STAR\*D/i.test(briefContext())) return {...fallback, title: "Dynamic-treatment-regime specialist, with LLM-assisted preparation", reason: "This question involves sequential decisions. The listed policytree tool is not a complete sequential-policy workflow; a specialist should review decision stages and available evidence."};
  if (task === "mediation" && /interventional|dependent|dependence|multiple mediators/i.test(briefContext())) return {...fallback, title: "Mediation specialist, with LLM-assisted preparation", reason: "This Brief involves mediator dependence or an interventional indirect-effect estimand. Confirm the estimand and joint mediator model before assuming the listed mediation package supports it."};
  if (task === "shift" && /synthesi|generation|contrast-to|non-contrast/i.test($("#prediction-target").value)) return {...fallback, reason: "This is image generation under shift. First use a capable LLM or specialist to specify the image target, reference data and evaluation, then check DG Copilot's fit rather than assuming a classification workflow applies."};
  const preparation = {
    effect: ["Causal-inference specialist, with LLM-assisted preparation", "A treatment contrast is framed, but identification and design remain to be assessed.", "Check the estimand, assignment process and assumptions first. Distinguish randomised, observational and instrumental-variable designs before selecting an estimator or software."],
    shift: ["ML / domain specialist, with LLM-assisted preparation", "Robustness across environments needs a task-fit and evaluation review, not a guaranteed causal solution.", "Review source and target data, acquisition shifts, baselines and held-out environments. Consider DG Copilot only if its supported workflow fits; DomainBed is a benchmark reference, not a ready-made segmentation or synthesis pipeline."],
    mediation: ["Mediation specialist, with LLM-assisted preparation", "A proposed pathway does not establish mediation or identify an indirect effect.", "Specify the estimand, time ordering and mediator-outcome confounding. Check whether the proposed models and estimand are supported before choosing a mediation package."],
    descriptive: ["Statistician or domain analyst, with LLM-assisted preparation", "Description is a valid non-causal task; no causal identification is required for the stated goal.", "Review measurements, denominators, missingness and sampling. Consider survey (R) only when weights, clusters or stratification require survey-aware analysis; ordinary records may need simpler descriptive tools."],
    discovery: ["Causal-discovery specialist, with LLM-assisted preparation", "The goal is reviewable candidate structures, not a graph certified as true.", "Check variable types, temporal constraints, latent confounding and sampling before selecting a compatible discovery algorithm. Report ambiguous directions and sensitivity to assumptions."],
    policy: ["Policy-learning specialist, with LLM-assisted preparation", "A policy requires credible action-effect evidence, an objective and feasible decisions; complete fields do not establish these.", "Distinguish single-stage from sequential decisions and check support, utility and constraints. Consider policytree only for a compatible reward-based decision-tree formulation; validate the policy before any deployment."],
    counterfactual: ["Structural-model specialist, with LLM-assisted preparation", "Same-case counterfactuals depend on structural and noise assumptions, not merely a plausible generated alternative.", "Check the factual case, intervention, fitted mechanisms and case-preserving noise inference. DoWhy GCM requires compatible structural mechanisms; MRI generation may require a specialised implementation such as DeepSCM, not a direct plug-in."],
    prediction: ["Predictive-modelling specialist, with LLM-assisted preparation", "Prediction without an intervention or shift question does not require causal identification.", "Review prediction-time availability, labels, leakage and validation. scikit-learn is a candidate for compatible predictive models; image, sequence or other specialised inputs may need a different implementation."],
  }[task];
  return preparation ? {title: preparation[0], reason: preparation[1], next: `${preparation[2]} ChatGPT or Claude can help turn this Brief into a plan for expert review. The tools below are candidates, not a verified selection.`} : fallback;
}

function renderRoute() {
  const box = $("#route-content");
  const editButton = $('.step-panel[data-panel="4"] .quiet');
  const copyButton = $("#copy-handoff");
  $("#copy-status").textContent = "";

  const handoff = currentHandoff();
  handoffSnapshot = handoff || "";
  const hasHandoff = Boolean(handoff);
  $("#route-tools").innerHTML = destinationNavigation();
  editButton.dataset.prev = directRouteTasks.has(task) ? "2" : "3";
  editButton.textContent = directRouteTasks.has(task) ? "Change task" : "Edit brief";
  copyButton.disabled = !hasHandoff || !$("#problem").value.trim();
  $("#route-summary-title").textContent = task === "other" ? "Scope and next steps" : ["descriptive", "prediction"].includes(task) ? "Is causality needed here?" : "Where causality can be applied";
  $("#route-next-title").textContent = task === "other" ? "Continue outside Nirvana" : "Choose one next step";
  $("#route-guidance").classList.toggle("hidden", task === "other");
  $("#route-summary").textContent = {
    shift: `For “${value("prediction-target")}”, causal framing can help distinguish target-related variation from changes in acquisition, population or environment. Your suspected shifts are: ${value("shift-sources")}. Review these hypotheses with a specialist and use them to design robustness tests. They do not prove invariance or guarantee better performance. DG Copilot's suitability for your specific research task still needs review.`,
    effect: `Causal methods may help frame whether ${value("exposure")} changes ${value("outcome")} relative to ${value("comparator")}. A specialist must assess confounding, data support and identification before interpreting an effect.`,
    mediation: `Causal mediation can help formulate whether ${value("mediator")} is part of a pathway from ${value("mediation-exposure")} to ${value("mediation-outcome")}. The pathway and identification assumptions still require review.`,
    descriptive: "This is currently a descriptive question. Causal methods are not required to report its measures; they become relevant if the question changes to why an outcome occurs or what an intervention would change.",
  }[task] || "Clarify the intended question before deciding whether causal methods are useful.";
  if (hasHandoff && confirmedRevision !== revision) $("#copy-status").textContent = "You can copy this draft now. It is labelled unreviewed; pending chat proposals are excluded.";
  copyButton.textContent = {
    other: "Copy referral note",
    shift: "Copy handoff and recommendation",
    mediation: "Copy mediation brief",
    descriptive: "Copy analysis brief",
  }[task] || (hasHandoff ? "Copy handoff prompt" : "Route only");

  if (task === "other") {
    $("#route-summary").textContent = "Your question is outside Nirvana's supported tasks, or its intended goal is not yet clear. We have not established where causality applies, and no task-specific causal tool or analysis is recommended. You can clarify the question with an expert or general-purpose AI, or return to change the task.";
    $("#copy-status").textContent = hasHandoff && $("#problem").value.trim() ? "Copies your question and a request for guidance, not a causal analysis brief." : "Add your question before copying a referral note.";
    box.innerHTML = `<div class="route-card"><h3>Referral note</h3><div class="prompt-preview">${escapeHtml(handoff)}</div></div>`;
    return;
  }

  if (additionalTasks[task]) {
    $("#route-summary").textContent = additionalTasks[task].summary;
    box.innerHTML = `<div class="route-card"><h3>${escapeHtml(taskLabel())}: specialist preparation</h3><div class="prompt-preview">${escapeHtml(handoff)}</div></div>`;
    return;
  }
  if (task === "effect") {
    box.innerHTML = `<div class="route-card"><h3>Capable LLM or methodologist</h3><div class="prompt-preview">${escapeHtml(handoff)}</div></div>`;
    return;
  }
  if (task === "shift") {
    box.innerHTML = `<div class="route-card"><h3>Robustness study handoff</h3><div class="prompt-preview">${escapeHtml(handoff)}</div></div>`;
    return;
  }
  if (task === "mediation") {
    box.innerHTML = `<div class="route-card"><h3>Continue with a causal mediation specialist or methodologist</h3><p>This is a causal question, but it needs specialist review of the target effect, time ordering, assumptions, identification, and analysis.</p><div class="prompt-preview">${escapeHtml(handoff)}</div></div>`;
    return;
  }
  if (task === "descriptive") {
    box.innerHTML = `<div class="route-card"><h3>Continue with descriptive analysis</h3><p>This question does not require a causal contrast as currently stated. The brief defines the cohort, measure, denominator, strata, time window, and limitations.</p><div class="prompt-preview">${escapeHtml(handoff)}</div></div>`;
    return;
  }
  box.innerHTML = '<div class="route-card"><h3>Clarify the intended research output</h3><p>Choose a supported framing task or consult a domain expert. No causal claim or analysis has been inferred.</p></div>';
}

function updateTask(nextTask, keepChat = false) {
  if (task !== nextTask) {
    problemConcepts = [];
    framingReviewed = false;
    $("#reasoning-note").value = "";
    if (taskFields[task] && fieldsProblem === $("#problem").value &&
        (draftState !== "loading" || taskFields[task].some(([id]) => $(`#${id}`).value.trim()))) {
      taskDrafts.set(task, Object.fromEntries(taskFields[task].map(([id]) => [id, $(`#${id}`).value])));
    }
    initialValues.forEach((_value, id) => { if (id !== "problem") $(`#${id}`).value = ""; });
    task = nextTask;
    fieldsProblem = $("#problem").value;
    const saved = taskDrafts.get(task);
    if (saved) (taskFields[task] || []).forEach(([id]) => { $(`#${id}`).value = saved[id] || ""; });
    briefChanged(keepChat);
  }
  $$(".choice").forEach((choice) => {
    const selected = choice.dataset.task === task;
    choice.classList.toggle("selected", selected);
    choice.setAttribute("aria-pressed", String(selected));
  });
  $("#agent-title").textContent =
    task === "shift" ? "Prepare a robustness study" : "Talk through the framing";
  $("#agent-message").placeholder =
    task === "shift"
      ? "For example: What should I clarify before using DG Copilot?"
      : "For example: What assumptions am I overlooking?";
  renderBrief();
  $("#task-next").disabled = categorising || !task;
}

function updateCount() {
  const reference = literatureExamples[selectedExample];
  $("#example-source").replaceChildren();
  if (reference) {
    const link = document.createElement("a");
    link.textContent = `Teaching example based on ${reference.citation}. Read the paper; this example does not reproduce its analysis.`;
    link.setAttribute("href", reference.url);
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
    $("#example-source").append(link);
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "Paper facts and teaching choices";
    details.append(summary);
    reference.provenance.forEach(item => {
      const paragraph = document.createElement("p");
      paragraph.textContent = `${item.status}: ${item.fields.join(", ")}. ${item.source}. ${item.note}`;
      const source = document.createElement("a");
      source.textContent = " Source";
      source.setAttribute("href", item.url);
      source.setAttribute("target", "_blank");
      source.setAttribute("rel", "noopener noreferrer");
      paragraph.append(source);
      details.append(paragraph);
    });
    $("#example-source").append(details);
  }
  $("#problem-preview").innerHTML = $("#problem").value.trim()
    ? NirvanaMarkdown.render($("#problem").value)
    : "<p>No content to preview yet.</p>";
  $("#count").textContent = $("#problem").value.length;
  $$(".example-button").forEach((button) => {
    const selected = button.dataset.example === selectedExample;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
}

function setProblemPreview(preview) {
  $("#problem").classList.toggle("hidden", preview);
  $("#problem-preview").classList.toggle("hidden", !preview);
  $("#problem-edit").setAttribute("aria-pressed", String(!preview));
  $("#problem-preview-toggle").setAttribute("aria-pressed", String(preview));
}
$("#problem-edit").addEventListener("click", () => {
  setProblemPreview(false);
  $("#problem").focus();
});
$("#problem-preview-toggle").addEventListener("click", () => {
  setProblemPreview(true);
  $("#problem-preview").focus();
});

$$('[data-next]').forEach((button) =>
  button.addEventListener("click", () => go(Number(button.dataset.next))),
);
$$('[data-prev]').forEach((button) =>
  button.addEventListener("click", () => go(Number(button.dataset.prev))),
);
$$('.step').forEach((button) =>
  button.addEventListener("click", () => go(Number(button.dataset.step))),
);
$$('.choice').forEach((button) =>
  button.addEventListener("click", () => {
    const regenerate = ["loading", "ready", "error"].includes(draftState) && task !== button.dataset.task && !taskDrafts.has(button.dataset.task);
    updateTask(button.dataset.task);
    if (regenerate) return requestFraming(true, true);
  }),
);
$$('.example-button').forEach((button) =>
  button.addEventListener("click", () => {
    startOwnQuestion();
    selectedExample = button.dataset.example;
    $("#problem").value = exampleProblems[selectedExample];
    briefChanged();
    renderBrief();
  }),
);

initialValues.forEach((_initialValue, id) => {
  $(`#${id}`).addEventListener("input", () => {
    editField(id, $(`#${id}`).value);
  });
});

function startOwnQuestion() {
  framingReviewed = false;
  $("#reasoning-note").value = "";
  setProblemPreview(false);
  taskDrafts.clear();
  awaitingTaskReview = false;
  $("#task-status").textContent = "";
  $("#retry-categorise").classList.add("hidden");
  $$(".choice").forEach((button) => {
    button.style.order = "";
    button.classList.remove("recommended");
  });
  initialValues.forEach((_value, id) => {
    $(`#${id}`).value = "";
    $(`#${id}`).placeholder = "Unknown / not provided";
  });
  selectedExample = null;
  updateTask(null);
  taskDrafts.clear();
  briefChanged();
  go(1);
}

$('[data-action="reset"]').addEventListener("click", startOwnQuestion);

$("#confirm-brief").addEventListener("click", () => {
  if (!taskFields[task] || !$("#problem").value.trim()) return;
  confirmedRevision = revision;
  renderReview();
  renderRoute();
});

$("#copy-handoff").addEventListener("click", async () => {
  if (!handoffSnapshot || !$("#problem").value.trim()) {
    $("#copy-status").textContent = "Enter a research question and select a supported task first.";
    return;
  }
  const copiedRevision = revision;
  try {
    await navigator.clipboard.writeText(handoffSnapshot);
    if (copiedRevision === revision) $("#copy-status").textContent = "Copied current Brief. Pending proposals were not included; review before sharing.";
  } catch {
    if (copiedRevision === revision) $("#copy-status").textContent =
      "Copy is unavailable in this browser. Select the preview text manually.";
  }
});

async function requestFraming(generate = false, draftOnly = false) {
  const input = $("#agent-message");
  const send = $('#agent-form button[type="submit"]');
  const text = generate ? $("#problem").value.trim() : input.value.trim();
  const worked = generate && literatureExamples[selectedExample]?.problem.trim() === text ? literatureExamples[selectedExample] : null;
  if (!text || pendingChat || (!generate && proposals.length)) return;

  if (generate) {
    problemConcepts = [];
    framingReviewed = false;
    clearChat();
    if (!draftOnly) taskDrafts.clear();
  }

  const request = new AbortController();
  pendingChat = request;
  renderBriefCheck();

  const history = chat.slice(-12).map(({role, text}) => ({role, text}));
  const userEntry = { role: "user", text };
  chat.push(userEntry);
  renderChat();
  input.value = "";
  input.disabled = true;
  send.disabled = true;
  $("#generate-brief").disabled = true;
  $("#agent-status").textContent = "Thinking...";
  $("#generation-status").textContent = "";
  if (generate && !draftOnly) {
    awaitingTaskReview = true;
    setCategorising(true);
    $$(".choice").forEach((button) => {
      button.style.order = "";
      button.classList.remove("recommended");
    });
    $("#task-status").textContent = "Nirvana is categorising your research question…";
    $("#retry-categorise").classList.add("hidden");
    go(2);
  }

  const timeout = setTimeout(() => request.abort(), 95000);
  try {
    if (text.length > (generate ? BRIEF_FIELD_LIMIT : 4000)) {
      throw new Error(`Keep ${generate ? "the research question" : "each message"} within ${generate ? "2,000" : "4,000"} characters. Your text was kept.`);
    }
    if (!generate) {
      const oversized = (taskFields[task] || []).find(([id]) => $(`#${id}`).value.length > BRIEF_FIELD_LIMIT);
      if (oversized) throw new Error(`${oversized[1]} exceeds the 2,000-character field limit. Shorten it before asking Nirvana for edits; your draft was kept.`);
    }
    const configuredApiBase = window.NIRVANA_API_BASE;
    if (configuredApiBase != null && configuredApiBase !== "" && configuredApiBase !== "/nirvana/api") {
      throw new Error('NIRVANA_API_BASE must be empty for the local demo or "/nirvana/api" for same-origin hosting.');
    }
    const apiBase = configuredApiBase || `http://${window.location.hostname || "127.0.0.1"}:8011/api`;
    if (generate && !draftOnly) {
      const classifiedResponse = await fetch(`${apiBase}/classify`, {
        signal: request.signal, method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: text, context: "Classify this new question only.", history: []}),
      });
      const classification = await classifiedResponse.json();
      if (pendingChat !== request) return;
      if (!classifiedResponse.ok || !(classification.task in taskFields || classification.task === "other")) throw new Error(classification.error || "Task classification failed. Please retry.");
      updateTask(classification.task, true);
      setCategorising(false);
      $$(".choice").forEach(button => {
        const recommended = button.dataset.task === task;
        button.style.order = recommended ? "-1" : "";
        button.classList.toggle("recommended", recommended);
      });
      $("#task-status").textContent = `Recommended: ${taskLabel()}. ${classification.reason || ""}`;
    }
    const selectedTask = task;
    if (generate && task === "other") {
      setDraftState("ready");
      $("#task-status").textContent = "No supported task identified. Click Next for referral options, or choose another task.";
      return;
    }
    if (generate) {
      setDraftState("loading", "Preparing Brief and concepts…");
      if (worked?.task === task) {
        (taskFields[task] || []).forEach(([id]) => { $(`#${id}`).value = worked.fields[id] || ""; });
        briefChanged(true);
        renderBrief();
      }
    }
    const outgoing = framingRequest({ message: text, ...(generate ? {selected_task: selectedTask} : {}), context: generate ? (worked ? `Paper-anchored teaching example. Use these authored specifications as context, retaining teaching labels and unresolved decisions. Explain relevant concepts. Specs: ${JSON.stringify(worked.fields)}` : "New question. Draft from this message only; previous worksheet values do not apply.") : briefContext(true), history });
    const response = await fetch(`${apiBase}/frame`, {
      signal: request.signal,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: outgoing.body,
    });
    const result = await response.json();
    if (pendingChat !== request) return;
    if (!response.ok) throw new Error(result.error || "The LLM request failed.");
    if (!(result.task in taskFields || result.task === 'other') ||
        !result.fields || typeof result.reply !== 'string') throw new Error("The server returned an invalid Brief. Your current draft was kept.");
    if (generate) {
      if (result.task !== selectedTask || task !== selectedTask) throw new Error("The draft did not match your selected task. Please retry.");
      initialValues.forEach((_value, id) => { if (id !== "problem") $(`#${id}`).value = ""; });
      const draftFields = worked?.task === task ? worked.fields : result.fields;
      (taskFields[task] || []).forEach(([id]) => { $(`#${id}`).value = draftFields[id] || ""; });
      fieldsProblem = $("#problem").value;
      briefChanged(true);
      renderBrief();
    } else if (result.task === task) {
      proposals = (taskFields[task] || []).map(([id, label]) => ({id, label, before: $(`#${id}`).value, after: (result.fields[id] || "").replace(/^\s*\[?unknown(?: \/ not provided)?\]?\s*$/i, "")}))
        .filter(({before, after}) => before.trim() !== after.trim());
      renderProposals();
    }
    const review = result.review && (taskFields[task] || []).some(([id]) => id === result.review.field_id) ? result.review : null;
    if (!briefCheck?.paused) {
      nextReview = review;
      if (briefCheck) briefCheck.question = "";
      syncReviewFocus();
    }
    chat.push({ role: "assistant", text: result.reply + (review ? `\n\n${review.question}` : ""),
      reviewQuestion: review?.question || null });
    if (result.task === task && Array.isArray(result.concepts)) {
      problemConcepts = result.concepts.filter(c => c && [c.title, c.definition, c.relevance].every(v => typeof v === "string")).slice(0, 4);
      renderFraming();
    }
    renderChat();
    $("#agent-status").textContent = [
      proposals.length ? "Review suggested changes below." : "",
      outgoing.omittedHistory ? "Earlier discussion messages were omitted from this request to fit its size limit. Your Brief and full on-screen discussion are unchanged." : "",
    ].filter(Boolean).join(" ");
    if (generate) setDraftState("ready");
  } catch (error) {
    if (pendingChat === request) {
      const index = chat.indexOf(userEntry);
      if (index >= 0) chat.splice(index, 1);
      renderChat();
      const message = error.name === "AbortError" ? "Request timed out. Your draft was kept; please retry." : (error.message || "Could not reach the Nirvana API. Check the service logs and API configuration.");
      $("#agent-status").textContent = message;
      $("#generation-status").textContent = message;
      if (generate && categorising) {
        $("#task-status").textContent = `${message} Retry, or choose a task manually and click Next.`;
        $("#retry-categorise").classList.remove("hidden");
      } else if (generate) setDraftState("error", `${message} Your selected task is kept. Retry generation or continue manually.`);
      if (!generate) input.value = text;
    }
  } finally {
    clearTimeout(timeout);
    if (pendingChat === request) {
      pendingChat = null;
      input.disabled = false;
      send.disabled = proposals.length > 0;
      $("#generate-brief").disabled = false;
      setCategorising(false);
      renderBriefCheck();
      // Closing the panel while ELM is running must not steal focus back.
      if ($("#chat-toggle").getAttribute("aria-expanded") === "true") input.focus();
    }
  }
}

$("#agent-message").addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || !event.ctrlKey || event.shiftKey || event.altKey || event.metaKey || event.isComposing) return;
  event.preventDefault();
  if (event.repeat || $('#agent-form button[type="submit"]').disabled) return;
  return requestFraming();
});

$("#agent-form").addEventListener("submit", (event) => {
  event.preventDefault();
  return requestFraming();
});
$("#generate-brief").addEventListener("click", () => {
  if (!$("#problem").value.trim()) {
    setProblemPreview(false);
    $("#generation-status").textContent = "Describe your research question first.";
    $("#problem").focus();
    return;
  }
  return requestFraming(true);
});

$("#retry-categorise").addEventListener("click", () => requestFraming(true));
$("#retry-draft").addEventListener("click", () => requestFraming(true, true));
$("#task-next").addEventListener("click", () => {
  if (categorising || !task) return;
  awaitingTaskReview = false;
  go(2.5);
});

$("#framing-next").addEventListener("click", () => {
  if (!task || categorising || awaitingTaskReview) return;
  framingReviewed = true;
  go(3);
});
$("#reasoning-note").addEventListener("input", () => briefChanged());
$("#discuss-reasoning").addEventListener("click", () => {
  toggleChat(true);
  if (pendingChat || proposals.length) {
    $("#agent-status").textContent = "Finish the current request or resolve its suggestions before discussing your reasoning.";
    return;
  }
  const note = $("#reasoning-note").value.trim();
  $("#agent-message").value = note
    ? `Please discuss my reasoning and uncertainty in relation to this research question. Explain what is plausible and what I may be misunderstanding, and help me apply the relevant concepts. My reasoning: ${note}`
    : "Help me reason about this specific research question. Explain the most relevant concept and ask one question to help me apply it.";
  return requestFraming();
});
for (const [id, label] of [["problem", "Research problem"], ...Object.values(taskFields).flat()]) {
  const control = $(`#${id}`);
  control.maxLength = BRIEF_FIELD_LIMIT;
  control.setAttribute("aria-describedby", "brief-field-limit");
  if (id === "problem") $('label[for="problem"] strong')?.append(fieldHelp(id, label));
  else control.parentElement?.insertBefore(fieldHelp(id, label), control);
}
startOwnQuestion();
