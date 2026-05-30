import Logo from './Logo.jsx';

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <Logo />
        <div className="auth-divider" />
        <h1>{title}</h1>
        <p>{subtitle}</p>
        {children}
      </section>
    </main>
  );
}
