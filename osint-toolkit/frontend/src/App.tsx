import { useState } from "react";
import { DomainIntelPanel } from "./features/domain-intel/DomainIntelPanel";
import { NetworkReconPanel } from "./features/network-recon/NetworkReconPanel";
import { SocialProfilingPanel } from "./features/social-profiling/SocialProfilingPanel";
import { BreachCheckPanel } from "./features/breach-check/BreachCheckPanel";
import { ReportBuilder } from "./features/report-engine/ReportBuilder";

const tabs = ["Domain Intel", "Network Recon", "Social Profiling", "Breach Check", "Report Engine"] as const;
type Tab = typeof tabs[number];

export default function App() { const [active, setActive] = useState<Tab>("Domain Intel"); const panel = { "Domain Intel": <DomainIntelPanel />, "Network Recon": <NetworkReconPanel />, "Social Profiling": <SocialProfilingPanel />, "Breach Check": <BreachCheckPanel />, "Report Engine": <ReportBuilder /> }[active]; return <main><header><p className="eyebrow">Academic investigation workspace</p><h1>OSINT Toolkit</h1><p>Run focused public-source checks or build a consolidated investigation report.</p></header><nav aria-label="Toolkit features">{tabs.map(tab => <button key={tab} className={active === tab ? "tab active" : "tab"} onClick={() => setActive(tab)}>{tab}</button>)}</nav>{panel}</main>; }
