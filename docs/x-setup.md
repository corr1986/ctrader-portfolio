# Setup X (Twitter) per la pipeline copyfunnel — guida passo-passo

Tempo stimato: 15-20 minuti, una tantum. Al termine la pipeline potrà pubblicare da sola.

## 1. Crea l'account X del brand

1. Vai su https://x.com e crea un nuovo account (proposta nome: **@XybridFX**, coerente col Myfxbook).
2. Bio suggerita: `Real-money automated FX trading. Every trade published hourly on GitHub. Not financial advice.` + link alla pagina cTrader Copy.
3. Immagine profilo: possiamo generarla dalla pipeline (stesso tema scuro del recap) — chiedimela.

## 2. Attiva l'accesso developer (piano Free)

1. Loggato con l'account del brand, vai su https://developer.x.com e clicca **Sign up for Free account**.
2. Descrivi l'uso quando richiesto (va bene: "Automated weekly performance recaps of my own trading account, posted to my own profile").
3. Il piano Free consente ~500 post/mese: più che sufficiente (noi ne facciamo ~5).

## 3. Genera le 4 chiavi

1. Nel Developer Portal apri il tuo progetto/app di default.
2. **Settings → User authentication settings → Set up**: scegli **Read and write**, tipo app "Web App, Automated App or Bot" (callback URL: `https://example.com`, website: il tuo GitHub — servono solo per il form).
3. **Keys and tokens**:
   - `API Key` e `API Key Secret` → copiali subito
   - `Access Token` e `Access Token Secret` → **Generate** (devono dire "Created with Read and Write permissions" — se dice Read only, rigenerali DOPO il passo 2)

## 4. Compila il file .env

Crea `copyfunnel/.env` (è già nel .gitignore, non finirà mai su GitHub):

```
X_API_KEY=la_tua_api_key
X_API_SECRET=il_tuo_api_secret
X_ACCESS_TOKEN=il_tuo_access_token
X_ACCESS_SECRET=il_tuo_access_secret
```

## 5. Test

```
cd ctrader-portfolio
python -m copyfunnel.weekly_recap            # dry-run: mostra il post senza pubblicare
python -m copyfunnel.weekly_recap --post     # pubblica davvero
```

## Altri punti del setup (non X)

- **Myfxbook pubblico**: su myfxbook.com → Settings → Portfolio → rendi pubblico il conto "xybridfx" e recupera il link pubblico (formato `myfxbook.com/members/...`). Poi lo aggiungiamo a descrizione e post.
- **Descrizione cTrader Copy**: incolla la versione EN da `docs/strategy-description.md` nella pagina della strategia.

## Limiti noti

- I depositi/prelievi appaiono come gradini nella curva balance/equity (es. il deposito del 24/06): AccountMonitor non li distingue dai profitti. Le statistiche del post sono trade-based e non ne risentono; il grafico sì. Miglioria futura: annotare i depositi sul grafico.
- Il P&L settimanale usa lo storico trade contenuto nello snapshot (ultimi ~67 trade): più che sufficiente per finestre di 7-30 giorni.
