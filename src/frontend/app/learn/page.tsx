// Seed concepts representative of the ECI knowledge graph
const FEATURED_CONCEPTS = [
  {
    id: 'structural_causal_model',
    name: 'Structural Causal Model',
    chapter: 2,
    desc: 'The formal language for encoding cause-and-effect via equations and graphs.',
  },
  {
    id: 'd_separation',
    name: 'd-Separation',
    chapter: 3,
    desc: 'A graphical criterion for reading conditional independence from a DAG.',
  },
  {
    id: 'backdoor_criterion',
    name: 'Backdoor Criterion',
    chapter: 4,
    desc: 'Identifies adjustment sets that block non-causal paths between variables.',
  },
  {
    id: 'identifiability',
    name: 'Identifiability',
    chapter: 4,
    desc: 'Whether a causal quantity can be recovered from observational data alone.',
  },
  {
    id: 'intervention',
    name: 'Intervention (do-calculus)',
    chapter: 4,
    desc: 'Pearl\'s do-operator models the effect of externally forcing a variable.',
  },
  {
    id: 'causal_discovery',
    name: 'Causal Discovery',
    chapter: 7,
    desc: 'Learning causal structure from data under various faithfulness assumptions.',
  },
  {
    id: 'counterfactual',
    name: 'Counterfactual',
    chapter: 5,
    desc: 'Reasoning about what would have happened under a different action.',
  },
  {
    id: 'additive_noise_model',
    name: 'Additive Noise Model',
    chapter: 7,
    desc: 'A restricted SCM class that enables identifiability from observational data.',
  },
]

export default function LearnPage() {
  return (
    <main>
      {/* Page header */}
      <div className="page-header">
        <div className="page-tag">
          <span className="page-tag-dot" />
          <span className="page-tag-text">Study Mode</span>
        </div>
        <h1 className="page-title">
          Concept<br />Explorer
        </h1>
        <p className="page-desc">
          Browse the ECI knowledge graph. Select any concept to see its
          prerequisites, related topics, and the sections it appears in.
        </p>
      </div>

      <div className="page-content">
        {/* Search placeholder */}
        <div className="search-bar">
          <span className="search-prefix">search:</span>
          <input
            className="search-input"
            type="text"
            placeholder="e.g. backdoor criterion, d-separation, SCM…"
            readOnly
          />
        </div>

        {/* Featured concepts grid */}
        <div className="concept-grid">
          {FEATURED_CONCEPTS.map((c) => (
            <div key={c.id} className="concept-card">
              <div className="concept-card-id">Ch.{c.chapter} · {c.id}</div>
              <div className="concept-card-name">{c.name}</div>
              <div className="concept-card-meta">{c.desc}</div>
            </div>
          ))}
        </div>

        <div className="coming-soon">
          <span className="coming-soon-icon">◈</span>
          Full concept explorer with graph traversal and AI explanations
          launches in Story 2.x
        </div>
      </div>
    </main>
  )
}
