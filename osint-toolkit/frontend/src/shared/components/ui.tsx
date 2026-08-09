import type { ButtonHTMLAttributes, PropsWithChildren } from "react";
export function Card({ children }: PropsWithChildren) { return <section className="card">{children}</section>; }
export function Button(props: ButtonHTMLAttributes<HTMLButtonElement>) { return <button className="button" {...props} />; }
export function Spinner() { return <span className="spinner" aria-label="Loading" />; }
export function ErrorBanner({ message }: { message: string }) { return <div className="error-banner" role="alert">{message}</div>; }
export function RawResponse({ value }: { value: unknown }) { return <details><summary>Raw response</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>; }
export function ResultTable({ rows }: { rows: Array<[string, unknown]> }) { return <div className="table-wrap"><table><tbody>{rows.map(([key, value]) => <tr key={key}><th>{key}</th><td>{Array.isArray(value) ? value.join(", ") || "—" : String(value ?? "—")}</td></tr>)}</tbody></table></div>; }
