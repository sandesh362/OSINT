import { useState } from "react";
import { DomainIntelPanel } from "./features/domain-intel/DomainIntelPanel";
import { NetworkReconPanel } from "./features/network-recon/NetworkReconPanel";
import { SocialProfilingPanel } from "./features/social-profiling/SocialProfilingPanel";
import { BreachCheckPanel } from "./features/breach-check/BreachCheckPanel";
import { ReportBuilder } from "./features/report-engine/ReportBuilder";
import { apiConfigurationError } from "./api/client";
import { ToolIcon, type ToolName } from "./shared/components/ToolIcon";
import { useBackendHealth } from "./shared/hooks/useBackendHealth";
const tools: {
    id: ToolName;
    label: string;
    description: string;
    panel: JSX.Element;
}[] = [
    { id: "domain", label: "Domain Intel", description: "WHOIS & DNS records", panel: <DomainIntelPanel /> },
    { id: "network", label: "Network Recon", description: "Hosts & exposed services", panel: <NetworkReconPanel /> },
    { id: "social", label: "Social Profiling", description: "Public username checks", panel: <SocialProfilingPanel /> },
    { id: "breach", label: "Breach Check", description: "Email exposure metadata", panel: <BreachCheckPanel /> },
    { id: "report", label: "Report Engine", description: "Consolidated findings", panel: <ReportBuilder /> },
];
export default function App() {
    const [active, setActive] = useState<ToolName>("domain");
    const backend = useBackendHealth();
    return (<div className="app-shell">
      <a className="skip-link" href="#workspace">Skip to workspace</a>
      <header className="app-header">
        <div className="header-inner">
          <a className="brand" href="./" aria-label="OSINT Toolkit home">
            <span className="brand-mark"><ToolIcon name="shield"/></span>
            <span>OSINT<span className="brand-light"> Toolkit</span></span>
          </a>
          <span className="header-label">Investigation workspace</span>
          <span className={`workspace-tag connection-${backend.status}`} role="status"><span aria-hidden="true"/> {backend.status === "connected" ? "Backend connected" : backend.status === "checking" ? "Connecting to backend…" : "Backend offline"}</span>
        </div>
      </header>
      <main id="workspace" tabIndex={-1}>
        <section className="workspace-intro" aria-labelledby="workspace-title">
          <div>
            <p className="eyebrow">RESEARCH. CONNECT. UNDERSTAND.</p>
            <h1 id="workspace-title">Intelligence starts here.</h1>
            <p className="intro-copy">Explore public sources, connect the evidence, and bring your findings together in one workspace.</p>
          </div>
          <div className="intro-note"><ToolIcon name="shield"/><span>Public data. Focused research.<br /><strong>Built for informed investigations.</strong></span></div>
        </section>
        {apiConfigurationError && <div className="error-banner" role="alert"><strong>Setup required.</strong> {apiConfigurationError}</div>}
        {!apiConfigurationError && backend.status === "offline" && <div className="error-banner" role="alert"><strong>Backend unavailable.</strong> Start the backend on port 8000, then <button type="button" className="retry-link" onClick={backend.retry}>retry connection</button>.</div>}
        <nav className="tool-nav" aria-label="Investigation tools">
          {tools.map((tool, index) => (<button key={tool.id} id={`tool-${tool.id}`} type="button" className={`tool-tab${active === tool.id ? " active" : ""}`} aria-pressed={active === tool.id} aria-controls={`panel-${tool.id}`} onClick={() => setActive(tool.id)}>
              <span className="tool-tab-top"><ToolIcon name={tool.id}/><span className="tool-number">0{index + 1}</span></span>
              <span className="tool-label">{tool.label}</span>
              <span className="tool-description">{tool.description}</span>
            </button>))}
        </nav>
        {tools.map(tool => (<div key={tool.id} id={`panel-${tool.id}`} role="region" aria-labelledby={`tool-${tool.id}`} hidden={active !== tool.id}>
            {tool.panel}
          </div>))}
        <footer className="workspace-footer">
          <span><ToolIcon name="shield"/> Research responsibly. Use findings within your authorized scope.</span>
          <span>OSINT Toolkit <span className="footer-divider">/</span> Investigation workspace</span>
        </footer>
      </main>
    </div>);
}
