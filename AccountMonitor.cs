using System;
using System.IO;
using System.Text;
using cAlgo.API;

/// <summary>
/// AccountMonitor — cBot di SOLA LETTURA per monitoraggio conto cTrader.
/// NON invia ordini. NON modifica posizioni. NON interagisce con altri bot.
/// Scrive uno snapshot JSON in C:\AccountMonitor\snapshot.json ogni X minuti.
/// </summary>
[Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.FileSystem)]
public class AccountMonitor : Robot
{
    [Parameter("Cartella output", DefaultValue = @"C:\AccountMonitor")]
    public string OutputFolder { get; set; }

    [Parameter("Intervallo (minuti)", DefaultValue = 30, MinValue = 5, MaxValue = 120)]
    public int IntervalMinutes { get; set; }

    protected override void OnStart()
    {
        Print("AccountMonitor avviato — solo lettura, nessun ordine.");
        WriteSnapshot();
        Timer.Start(IntervalMinutes * 60);
    }

    protected override void OnTimer()
    {
        WriteSnapshot();
        Timer.Start(IntervalMinutes * 60);
    }

    protected override void OnStop()
    {
        WriteSnapshot();
        Print("AccountMonitor fermato.");
    }

    private void WriteSnapshot()
    {
        try
        {
            // --- Dati conto ---
            double balance = Account.Balance;
            double equity = Account.Equity;
            double unrealizedPnl = equity - balance;
            string currency = Account.Currency;

            // --- Posizioni aperte ---
            var posJson = new StringBuilder();
            posJson.Append("[");
            bool first = true;
            foreach (var pos in Positions)
            {
                if (!first) posJson.Append(",");
                string sl = pos.StopLoss.HasValue ? pos.StopLoss.Value.ToString("F5") : "null";
                string tp = pos.TakeProfit.HasValue ? pos.TakeProfit.Value.ToString("F5") : "null";
                posJson.AppendFormat(@"{{
  ""id"": {0},
  ""symbol"": ""{1}"",
  ""direction"": ""{2}"",
  ""lots"": {3},
  ""entry_price"": {4},
  ""current_price"": {5},
  ""pnl"": {6:F2},
  ""pips"": {7:F1},
  ""sl"": {8},
  ""tp"": {9},
  ""label"": ""{10}"",
  ""open_time"": ""{11:yyyy-MM-ddTHH:mm:ss}""
}}",
                    pos.Id,
                    pos.SymbolName,
                    pos.TradeType,
                    pos.Quantity.ToString("F2"),
                    pos.EntryPrice.ToString("F5"),
                    pos.SymbolCurrentBid.ToString("F5"),
                    pos.NetProfit,
                    pos.Pips,
                    sl,
                    tp,
                    pos.Label ?? "",
                    pos.EntryTime
                );
                first = false;
            }
            posJson.Append("]");

            // --- Storico trade chiusi (ultimi 100) ---
            var histJson = new StringBuilder();
            histJson.Append("[");
            first = true;
            int count = 0;
            double realizedPnl = 0;
            int wins = 0, losses = 0;

            foreach (var trade in History)
            {
                realizedPnl += trade.NetProfit;
                if (trade.NetProfit > 0) wins++;
                else losses++;

                if (count < 100)
                {
                    if (!first) histJson.Append(",");
                    histJson.AppendFormat(@"{{
  ""id"": {0},
  ""symbol"": ""{1}"",
  ""direction"": ""{2}"",
  ""lots"": {3},
  ""entry_price"": {4},
  ""close_price"": {5},
  ""pnl"": {6:F2},
  ""pips"": {7:F1},
  ""open_time"": ""{8:yyyy-MM-ddTHH:mm:ss}"",
  ""close_time"": ""{9:yyyy-MM-ddTHH:mm:ss}""
}}",
                        trade.PositionId,
                        trade.SymbolName,
                        trade.TradeType,
                        trade.Quantity.ToString("F2"),
                        trade.EntryPrice.ToString("F5"),
                        trade.ClosingPrice.ToString("F5"),
                        trade.NetProfit,
                        trade.Pips,
                        trade.EntryTime,
                        trade.ClosingTime
                    );
                    first = false;
                    count++;
                }
            }
            histJson.Append("]");

            double winRate = (wins + losses) > 0 ? (double)wins / (wins + losses) * 100 : 0;

            // --- JSON finale ---
            string json = string.Format(@"{{
  ""timestamp"": ""{0:yyyy-MM-ddTHH:mm:ss}"",
  ""account_number"": ""{1}"",
  ""currency"": ""{2}"",
  ""balance"": {3:F2},
  ""equity"": {4:F2},
  ""unrealized_pnl"": {5:F2},
  ""realized_pnl"": {6:F2},
  ""open_positions"": {7},
  ""total_trades"": {8},
  ""wins"": {9},
  ""losses"": {10},
  ""win_rate"": {11:F1},
  ""positions"": {12},
  ""history"": {13}
}}",
                DateTime.UtcNow,
                Account.Number,
                currency,
                balance,
                equity,
                unrealizedPnl,
                realizedPnl,
                Positions.Count,
                wins + losses,
                wins,
                losses,
                winRate,
                posJson.ToString(),
                histJson.ToString()
            );

            // --- Scrittura file ---
            if (!Directory.Exists(OutputFolder))
                Directory.CreateDirectory(OutputFolder);

            string outputPath = Path.Combine(OutputFolder, "snapshot.json");
            File.WriteAllText(outputPath, json, Encoding.UTF8);

            Print(string.Format("Snapshot scritto: Balance={0:F2} Equity={1:F2} Pos={2}",
                balance, equity, Positions.Count));
        }
        catch (Exception ex)
        {
            Print("AccountMonitor ERROR: " + ex.Message);
        }
    }
}
