import TeluguEditor from "./components/Editor/TeluguEditor";
import SpellCorrectionPanel from "./components/SpellCorrection/SpellCorrectionPanel";
import GrammarCorrectionPanel from "./components/GrammarCorrection/GrammarCorrectionPanel";
import TransliteratorPanel from "./components/Transliterator/TransliteratorPanel";
import { useState, useEffect } from "react";
import { healthCheck } from "./api/client";

export default function App() {
  const [status, setStatus] = useState("connecting");
  const [activeTab, setActiveTab] = useState("spell");

  useEffect(() => {
    healthCheck()
      .then((data) => {
        setStatus(`online — ${data.dictionary_size} words`);
      })
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <div className="app-root">
      {/* ── Animated background ─────────────────────────────────── */}
      <div className="bg-gradient" />
      <div className="bg-noise" />

      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-inner">
          <div className="logo-group">
            <span className="logo-icon">తె</span>
            <div>
              <h1 className="app-title">Telugu Writing Assistant</h1>
              <p className="app-subtitle">
                స్మార్ట్ తెలుగు రాత సహాయకుడు
              </p>
            </div>
          </div>
          <div className={`status-pill ${status.includes("online") ? "online" : "offline"}`}>
            <span className="status-dot" />
            <span>{status}</span>
          </div>
        </div>
      </header>

      {/* ── Tab navigation ──────────────────────────────────────── */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === "spell" ? "active" : ""}`}
          onClick={() => setActiveTab("spell")}
        >
          <span className="tab-icon">🔴</span>
          <span>Spell Check</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "grammar" ? "active" : ""}`}
          onClick={() => setActiveTab("grammar")}
        >
          <span className="tab-icon">🔵</span>
          <span>Grammar Check</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "transliterate" ? "active" : ""}`}
          onClick={() => setActiveTab("transliterate")}
        >
          <span className="tab-icon">🔤</span>
          <span>Transliterator</span>
        </button>
      </nav>

      {/* ── Main content ────────────────────────────────────────── */}
      <main className="main-content">
        {activeTab === "spell" && (
          <div className="panel-animate">
            <SpellCorrectionPanel />
          </div>
        )}

        {activeTab === "grammar" && (
          <div className="panel-animate">
            <GrammarCorrectionPanel />
          </div>
        )}

        {activeTab === "transliterate" && (
          <div className="panel-animate">
            <TransliteratorPanel />
          </div>
        )}
      </main>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer className="app-footer">
        <p>
          Built with FastAPI · React · Hand-crafted NLP — No external ML
          libraries
        </p>
      </footer>
    </div>
  );
}
