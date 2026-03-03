const SPRINTS = [
  {
    num: '01',
    week: 'Week 1',
    name: 'Probabilistic Foundations',
    concepts: 'Random variables · Conditional independence · Markov condition',
    status: 'Upcoming',
  },
  {
    num: '02',
    week: 'Week 2',
    name: 'Structural Causal Models',
    concepts: 'SCMs · DAGs · Functional causal models · Acyclicity',
    status: 'Upcoming',
  },
  {
    num: '03',
    week: 'Week 3',
    name: 'Interventions & Identifiability',
    concepts: 'do-calculus · Backdoor criterion · Front-door criterion',
    status: 'Upcoming',
  },
  {
    num: '04',
    week: 'Week 4',
    name: 'Counterfactuals',
    concepts: 'Potential outcomes · PNS · ETT · Mediation',
    status: 'Upcoming',
  },
  {
    num: '05',
    week: 'Week 5',
    name: 'Causal Discovery',
    concepts: 'PC algorithm · FCI · ANM · LiNGAM · GES',
    status: 'Upcoming',
  },
]

export default function AgilePage() {
  return (
    <main>
      {/* Page header */}
      <div className="page-header">
        <div className="page-tag">
          <span className="page-tag-dot" />
          <span className="page-tag-text">Agile Mode</span>
        </div>
        <h1 className="page-title">
          Sprint-Based<br />Mastery
        </h1>
        <p className="page-desc">
          Learn causal inference through structured weekly sprints — each
          building on the last, tracked with AI-assisted progress reviews.
        </p>
      </div>

      <div className="page-content">
        {/* Sprint list */}
        <div className="sprint-list">
          {SPRINTS.map((s) => (
            <div key={s.num} className="sprint-item">
              <div className="sprint-num">{s.num}</div>
              <div className="sprint-info">
                <div className="sprint-week">{s.week}</div>
                <div className="sprint-name">{s.name}</div>
                <div className="sprint-concepts">{s.concepts}</div>
              </div>
              <div className="sprint-badge">{s.status}</div>
            </div>
          ))}
        </div>

        <div className="coming-soon">
          <span className="coming-soon-icon">◈</span>
          AI sprint reviews, adaptive pacing, and progress tracking launch
          in Story 3.x
        </div>
      </div>
    </main>
  )
}
