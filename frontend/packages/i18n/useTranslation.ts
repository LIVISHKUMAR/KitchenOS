import { useState, useCallback } from 'react';
import { t, type Language, translations } from './translations';

const STORAGE_KEY = 'kitchenos_language';

export function useTranslation() {
  const [language, setLanguageState] = useState<Language>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return (stored && stored in translations) ? stored as Language : 'en';
  });

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem(STORAGE_KEY, lang);
  }, []);

  const translate = useCallback((key: string) => {
    return t(key, language);
  }, [language]);

  return {
    language,
    setLanguage,
    t: translate,
    languages: Object.keys(translations) as Language[],
  };
}

export const languageNames: Record<Language, string> = {
  en: 'English',
  hi: 'हिन्दी',
  ta: 'தமிழ்',
  te: 'తెలుగు',
};
