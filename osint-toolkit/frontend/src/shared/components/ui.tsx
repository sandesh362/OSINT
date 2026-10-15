import { useId, type ButtonHTMLAttributes, type InputHTMLAttributes, type PropsWithChildren } from "react";
import { ToolIcon, type ToolName } from "./ToolIcon";
export function Card({ children }: PropsWithChildren) { return <section className="card">{children}</section>; }
export function Button({ children, className = "", disabled, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
    return <button className={`button ${className}`} disabled={disabled} aria-busy={disabled || undefined} {...props}>{children}</button>;
}
export function Field({ label, ...props }: InputHTMLAttributes<HTMLInputElement> & {
    label: string;
}) {
    const id = useId();
    return <div className="field"><label htmlFor={id}>{label}</label><input {...props} id={id}/></div>;
}
export function PanelHeading({ icon, title, description }: {
    icon: ToolName;
    title: string;
    description: string;
}) {
    return <div className="panel-heading"><span className="panel-icon"><ToolIcon name={icon}/></span><div><h2>{title}</h2><p>{description}</p></div></div>;
}
export function EmptyState({ icon, title, description }: {
    icon: ToolName;
    title: string;
    description: string;
}) {
    return <div className="empty-state"><span className="empty-icon"><ToolIcon name={icon}/></span><h3>{title}</h3><p>{description}</p></div>;
}
export function Spinner() { return <span className="loading-indicator" role="status"><span className="spinner" aria-hidden="true"/> Working…</span>; }
export function ErrorBanner({ message }: {
    message: string;
}) { return <div className="error-banner" role="alert">{message}</div>; }
export function RawResponse({ value }: {
    value: unknown;
}) { return <details><summary>View raw response</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>; }
export function ResultTable({ rows }: {
    rows: Array<[
        string,
        unknown
    ]>;
}) { return <div className="table-wrap"><table><tbody>{rows.map(([key, value]) => <tr key={key}><th scope="row">{key.replace(/_/g, " ")}</th><td>{Array.isArray(value) ? value.join(", ") || "—" : String(value ?? "—")}</td></tr>)}</tbody></table></div>; }
