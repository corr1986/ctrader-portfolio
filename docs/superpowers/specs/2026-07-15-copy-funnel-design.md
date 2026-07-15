# Copy Funnel — Design

**Data:** 2026-07-15
**Stato:** Approvato dall'utente (conversazione Cowork 15/07/2026)
**Obiettivo:** portare copiatori alla pagina cTrader Copy tramite contenuti automatici di performance.

## Contesto

- Pagina cTrader Copy attiva: strategia 115617 (`https://ct.spotware.com/copy/strategy/115617`), performance fee 15%, management 0%, volume 0.
- Conto reale cTrader n. 2121691 (EUR), due strategie con label separate: TRFX (segnali) e GridMartingala v6 (grid + RSI Daily).
- Dati già disponibili in questo repo: `account_snapshot.json` aggiornato ogni ora dalla VPS (AccountMonitor.cs → update_portfolio.py); lo storico git del file (~1.500 commit da fine maggio 2026) fornisce la serie temporale balance/equity.
- Myfxbook collegato (portfolio "xybridfx", id 12050062) ma **non ancora pubblico**: da rendere pubblico nelle impostazioni privacy per usarlo come verifica indipendente.
- Vincolo operativo: Claude non può creare account né gestire credenziali; l'utente fa il setup una tantum (account X developer, privacy Myfxbook), Claude costruisce e gestisce la pipeline.

## Decisioni

1. **Prodotto di monetizzazione = copy trading** (già live). Niente vendita di segnali: si condividono solo performance aggregate.
2. **Canale di distribuzione = X/Twitter** (pubblico FinTwit, formato nativo grafico+numeri, unico grande social interamente automatizzabile via API). Telegram per i copiatori rimandato a quando ci saranno copiatori (Fase 3).
3. **Lingua dei post: inglese** (il pubblico copy trading/FinTwit è globale; la portata in italiano sarebbe una frazione). Facile aggiungere versione italiana in seguito.
4. **Onestà come posizionamento:** si pubblicano anche i periodi negativi; nessuna promessa di rendimenti. È sia un obbligo etico sia la strategia di differenziazione credibile nel niche.

## Fasi

### Fase 1 — Descrizione strategia (subito, nessun setup)
Testo ottimizzato per la pagina copy (EN + IT), onesto sul profilo di rischio
(grid senza SL su parte delle posizioni), consegnato pronto da incollare.

### Fase 2 — Pipeline contenuti X (questo repo, cartella `copyfunnel/`)

Componenti, ognuno con responsabilità singola:

| Modulo | Responsabilità | Input | Output |
|---|---|---|---|
| `history.py` | Ricostruisce la serie equity/balance dallo storico git di `account_snapshot.json`, con cache incrementale | repo git | `equity_history.csv` |
| `stats.py` | Statistiche aggregate: ROI settimana/mese, max drawdown, win rate, trade count, per periodo | csv + snapshot | dict statistiche |
| `render.py` | Immagine recap (equity curve + riquadro statistiche, tema scuro pulito) | dict + csv | PNG |
| `compose.py` | Testo del post (EN), con link alla pagina copy e disclaimer | dict | stringa |
| `post_x.py` | Pubblicazione via X API v2 (tweepy); **dry-run di default** finché mancano le chiavi | PNG + testo | tweet |
| `weekly_recap.py` | Orchestratore CLI (`--dry-run` / `--post`) | — | — |

Flusso dati: git history → csv → stats → (render, compose) → post_x.

- Credenziali X in `copyfunnel/.env` (gitignored), mai nel codice.
- La pipeline è **sola lettura** sui dati di trading: non tocca bridge, VPS, né update_portfolio.py.
- Modalità approvazione: all'inizio ogni post viene generato in dry-run e mostrato all'utente; il passaggio a pubblicazione schedulata automatica è una decisione successiva esplicita.

### Fase 3 — Telegram copiatori (futuro)
Canale gratuito che riusa render/compose per aggiornare i copiatori. Si attiva quando esistono copiatori. Costo marginale ~zero.

## Gestione errori

- Snapshot mancante o stantio (>24h): la pipeline si ferma con messaggio chiaro, nessun post con dati vecchi.
- Git non raggiungibile: si usa la cache csv esistente, con nota nel log.
- Post X fallito: nessun retry automatico (evita doppi post); errore riportato.

## Test (pytest, TDD)

- `stats.py` e `compose.py`: test unitari su dati sintetici (casi: settimana positiva, negativa, senza trade, drawdown).
- `history.py`: test su repo git temporaneo sintetico.
- `render.py`: smoke test (il PNG viene creato, dimensioni > 0).
- Nessun test tocca l'API X reale: `post_x.py` testato solo in dry-run con mock.

## Setup a carico dell'utente (una tantum)

1. Rendere pubblico il portfolio Myfxbook (Settings → Privacy) e fornire il link pubblico.
2. Incollare la descrizione strategia nella pagina cTrader Copy (Fase 1).
3. Creare account X per il brand (proposta: nome coerente con "xybridfx") + account developer (developer.x.com, piano Free) e fornire le 4 chiavi da mettere in `.env`.

## Fuori scope

Streaming, vendita segnali, Darwinex/Collective2, Instagram (eventuale riuso ReelFactory in futuro), automazione della pubblicazione senza approvazione utente.
