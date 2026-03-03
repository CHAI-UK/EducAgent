import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { Cormorant_Garamond, JetBrains_Mono } from 'next/font/google'
import GraphBackground from '../components/GraphBackground'
import './globals.css'

const display = Cormorant_Garamond({
  weight: ['300', '400', '600'],
  style: ['normal', 'italic'],
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const mono = JetBrains_Mono({
  weight: ['300', '400', '500'],
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'EducAgent — Causal Inference Navigator',
  description:
    'AI-powered guide through Elements of Causal Inference (Peters et al., 2017)',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable}`}>
      <body>
        {/* Full-viewport animated causal graph backdrop */}
        <GraphBackground />

        <header className="site-header">
          <nav className="nav-inner">
            <a href="/" className="nav-brand">
              <span className="brand-hex">⬡</span>
              <span className="brand-name">EducAgent</span>
            </a>

            <div className="nav-links">
              <a href="/learn" className="nav-link">Study</a>
              <div className="nav-divider" />
              <a href="/graph" className="nav-link">Graph</a>
              <div className="nav-divider" />
              <a href="/agile" className="nav-link">Agile</a>
            </div>
          </nav>
        </header>

        <div className="page-wrap">{children}</div>

        <footer className="site-footer">
          Elements of Causal Inference · Peters, Janzing &amp; Schölkopf · 2017
        </footer>
      </body>
    </html>
  )
}
