export default function HomePage() {
  return (
    <main>
      <section className="hero">
        {/* Eyebrow */}
        <div className="hero-eyebrow">
          <span className="hero-eyebrow-line" />
          <span className="hero-eyebrow-text">
            AI-Powered Knowledge Navigator
          </span>
        </div>

        {/* Title */}
        <h1 className="hero-title">
          Navigate<br />
          <em className="hero-title-em">Causal</em><br />
          Inference
        </h1>

        {/* Tagline */}
        <p className="hero-sub">
          An intelligent guide through{' '}
          <em>Elements of Causal Inference</em> — 189 concepts,
          332 relationships, structured as a queryable knowledge graph.
        </p>

        {/* CTAs */}
        <div className="hero-actions">
          <a href="/learn" className="btn-gold">
            → Study Mode
          </a>
          <a href="/agile" className="btn-ghost">
            Agile Mode
          </a>
        </div>

        {/* Stats strip */}
        <div className="stats-strip">
          <div className="stat">
            <span className="stat-value">189</span>
            <span className="stat-label">Concepts</span>
          </div>
          <div className="stat">
            <span className="stat-value">332</span>
            <span className="stat-label">Relationships</span>
          </div>
          <div className="stat">
            <span className="stat-value">9</span>
            <span className="stat-label">Categories</span>
          </div>
          <div className="stat">
            <span className="stat-value">7</span>
            <span className="stat-label">Chapters</span>
          </div>
        </div>
      </section>
    </main>
  )
}
