# GL Workflow Transitions (Verifiziert 26.05.2026)

## Problem-Type (ID 10045)

| Status | Verfügbare Transitionen | Nächster Status |
|--------|------------------------|----------------|
| Offen (1) | ID 11: "Beginnen" | In Arbeit (3) |
| In Arbeit (3) | ID 21: "Vollständig", ID 131: "Eskalieren", ID 141: "Zurück zum Kunden" | Erledigt (5) |
| Erledigt (5) | Nur "Erneut öffnen" | In Arbeit (3) |

**Abschluss-Workflow:**
1. Beginnen (ID 11) → In Arbeit
2. Vollständig (ID 21) → Erledigt ✅

## Suggestion-Type (ID 10046)

| Status | Verfügbare Transitionen | Nächster Status |
|--------|------------------------|----------------|
| Offen | ID 4: "Fortschritt starten" | In Arbeit |
| In Arbeit | ID 5: "Vorgang lösen", ID 2: "Vorgang schließen" | Erledigt / Geschlossen |
| Erledigt | ID 2: "Vorgang schließen" | Geschlossen |

**Abschluss-Workflow:**
1. Fortschritt starten (ID 4) → In Arbeit
2. Vorgang lösen (ID 5) → Erledigt
3. Vorgang schließen (ID 2) → Geschlossen ✅

## Key Learnings

- **NIE blind `transition="Done"` verwende** — Jira Cloud in Dütsch brucht "Vorgang schließen", "Vorgang lösen", "Vollständig", etc.
- **Problem-Typ** hend kein direkti "Vorgang schließen"-Transition. Immer über In Arbeit → Vollständig.
- **Suggestion-Typ** hend "Vorgang lösen" (ID 5) + "Vorgang schließen" (ID 2) als eigenständigi Optione.
- **ID 21 "Vollständig"** wird ERST sichtbar, nachdem ID 11 "Beginnen" duuregführt worde isch.
- **ID 21 existiert nur für Problem-Type**, nöd für Suggestion.
