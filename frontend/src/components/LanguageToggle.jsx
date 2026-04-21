import useMissionStore from '../stores/missionStore'

export default function LanguageToggle() {
  const locale = useMissionStore(s => s.locale)
  const setLocale = useMissionStore(s => s.setLocale)

  return (
    <div className="flex gap-1 text-xs">
      <button
        onClick={() => setLocale('bm')}
        className="px-2 py-1 rounded transition-colors"
        style={{
          background: locale === 'bm' ? '#00D4FF' : '#1E3A5F',
          color: locale === 'bm' ? '#0B1426' : '#C4D4E6',
        }}
        title="Bahasa Malaysia"
      >BM</button>
      <button
        onClick={() => setLocale('en')}
        className="px-2 py-1 rounded transition-colors"
        style={{
          background: locale === 'en' ? '#00D4FF' : '#1E3A5F',
          color: locale === 'en' ? '#0B1426' : '#C4D4E6',
        }}
        title="English"
      >EN</button>
    </div>
  )
}
