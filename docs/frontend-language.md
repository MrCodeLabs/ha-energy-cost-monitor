# Frontend language support — 2 November 2026

English is the source/default language of the bundled card and automatic panel.
The HA user's locale language (or language field on older frontend objects)
selects Slovenian for `sl`/`sl-SI`; other languages fall back to English.
Native HA configuration forms already have English source strings and Slovenian
translations. No extra language setting, network request or package is required.

Labels, help, actions, accessibility labels, errors and interpolated messages use
the bundled dictionary. Numbers/dates use en-GB or sl-SI display conventions;
measurement timestamps and stored values are unchanged. Native numeric/date inputs
may follow the browser/OS conventions. Technical evidence codes, user-entered
names, sensor states, existing source attribution and frozen reports are not
rewritten. Newly created generic source attribution uses English.

Language changes preserve current controls, expanded sections, drafts and selected
upload files. Translation values are inserted as text, never HTML. The default
card-picker description is English. English public guidance uses English actions;
Slovenian documentation remains an optional translation. Historical evidence keeps
its original wording and identifies the revision it tested.

Validation: card syntax and behavior checks exercise all tabs, English/Slovenian,
regional language variants, unsupported-language fallback, error retranslation,
placeholder insertion, draft/file retention and native translation-key parity.
A local browser with synthetic data verified English study/EV forms and an
English → Slovenian → English price draft with its value retained. This is a
standalone frontend preview, not a fresh HA/HACS installation or backend test.
No production changes, storage migrations, publication or release in this step.
