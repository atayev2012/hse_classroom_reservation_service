import logoUrl from '../assets/img/HSE_logo.png';

export default function Logo({ compact = false }) {
  return (
    <div className={`brand-logo ${compact ? 'brand-logo--compact' : ''}`}>
      <img src={logoUrl} alt="НИУ ВШЭ Нижний Новгород" />
    </div>
  );
}
