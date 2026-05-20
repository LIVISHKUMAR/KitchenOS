import React from 'react';
import { useTranslation, languageNames, type Language } from '@kitchenos/i18n';

export const LanguageSwitcher: React.FC = () => {
  const { language, setLanguage, languages } = useTranslation();

  return (
    <select
      value={language}
      onChange={e => setLanguage(e.target.value as Language)}
      className="text-sm bg-transparent border-none cursor-pointer text-gray-500 hover:text-gray-700"
      title="Language"
    >
      {languages.map(lang => (
        <option key={lang} value={lang}>{languageNames[lang]}</option>
      ))}
    </select>
  );
};
