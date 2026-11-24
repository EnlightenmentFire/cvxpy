# "The Original Turtle Trading Rules" (Curtis Faith / OriginalTurtles.org): verbatim extracts for the fact-check

Compiled 2026-11-24. Each quote was pulled by script from the PDF text layer (pdftotext). Only running headers and page numbers were removed, and wrapped lines were re-joined. The formulas, the title pages and the passages where a sidebar is interleaved with body text were also checked against rendered page images.

## Sources used

| Label | What it is | URL | Notes |
|---|---|---|---|
| **[A]** | Earliest build I found. PDF metadata: Title "Original Turtle Rules"; Author "Curtis M. Faith with help from many others"; made with Acrobat PDFMaker 5.0 for Word; **created 2003-04-09**. 39 PDF pages (35 numbered). Written in the **third person** ("they"). | https://www.tradingblox.com/tbforum/download/file.php?id=5719 | md5 2568b9c246ee7031f98f940c4d9990d8 |
| **[B]** | Revised edition written in the **first person** ("we/us"). This file is a 2013-01-16 re-render (PDFCreator/Ghostscript) of "OriginalTurtleRules.pdf"; Author "Curtis M. Faith". 38 PDF pages (34 numbered). | https://tradingwithrayner.com/wp-content/uploads/2014/11/OriginalTurtleRules.pdf and https://therobusttrader.com/wp-content/uploads/OriginalTurtle-Trading-Rules.pdf | Both URLs serve byte-identical files (md5 2520989cc7b2d22194127b9fd2033a8a), so they count as one copy, not two. |
| **[C]** | Current download on Trading Blox's "Original Turtles" page: Nitro Pro build dated 2014-12-06, copy-protected, 27 pages. **Chapters 1–8 only, with no Foreword and no Introduction.** Its wording matches [B] on every page I checked. | https://www.tradingblox.com/originalturtles/originalturtlerules.pdf (linked from https://www.tradingblox.com/originalturtles/originalturtlerules.htm) | There is no text layer, so I checked it visually on printed pp. 7–8, 13–14, 16–22 and 25–26. |

Sources I could not reach:
- The Wayback copy of the original site file, http://web.archive.org/web/20031115032032/http://www.originalturtles.org:80/docs/turtlerules.pdf. The archive.org availability API confirms a snapshot from 2003-11-15 exists. However, curl through the proxy was reset, WebFetch refuses the domain, and Exa had no cached copy. **It is therefore UNVERIFIED which edition (A or B) originalturtles.org served, and when.**
- http://bigpicture.typepad.com/comments/files/turtlerules.pdf now redirects to a Network Solutions 403 page, so this mirror is dead.

Page numbers below are the printed folio numbers of each edition. From B's p.16 onward, [A] runs one page later than [B]. From Chapter 1 onward, [C] runs one page earlier than [B].

**How the editions differ, in short:** the rules themselves are identical in A, B and C: every number, threshold, and entry, exit and stop rule. B and C are a light copy-edit of A that switches from "they" to "we" and rewords a few sentences. I note each difference wherever it touches a requested quote.

---

## 1. N, True Range and the formula
Section: Chapter 3 "Position Sizing" → "Volatility – The Meaning of N". [A] pp.13–14, [B] pp.13–14, [C] p.13.

> The Turtles used a concept that Richard Dennis and Bill Eckhardt called N to represent the underlying volatility of a particular market.

(A = B)

> N is simply the 20-day exponential moving average of the True Range, which is now more commonly known as the ATR. Conceptually, N represents the average range in price movement that a particular market makes in a single day, accounting for opening gaps. N was measured in the same points as the underlying contract.

([B] = [C]. [A] is identical except that it has no comma after "True Range".)

True Range (A = B = C; checked on page images):
> To compute the daily true range:
> **True Range = Maximum(H - L, H - PDC, PDC - L)**
> where:
> H – Current High
> L – Current Low
> PDC – Previous Day’s Close

N formula (A = B = C; checked on page images; the original sets it as a fraction):
> To compute N use the following formula:
> **N = (19 × PDN + TR) / 20**
> where:
> PDN – Previous Day’s N
> TR – Current Day’s True Range

Seed value:
> [B]/[C]: Since this formula requires a previous day’s N value, you must start with a 20-day simple average of the True Range for the initial calculation.

> [A]: Since this formula requires a previous day’s N value one must start with a 20-day simple average of the True Range for the initial calculation.

Dollar volatility (A = B = C):
> This sounds more complicated than it is. It is determined using the simple formula:
> **Dollar Volatility = N × Dollars per Point**

**Verdict:** matches the brief. (My note, not the document's: weighting the previous value by 19/20 and the new True Range by 1/20 is Wilder-style smoothing. The document itself calls N a "20-day exponential moving average".)

## 2. Unit sizing
Section: Chapter 3. In [A] (p.15) the heading is "Units – Volatility Adjusted Position Units". In [B] (p.15) and [C] (p.14) it is "Volatility Adjusted Position Units". The table of contents calls it "Units".

> [B]/[C]: The Turtles built positions in pieces which we called Units. Units were sized so that 1 N represented 1% of the account equity.

> [A]: The Turtles built positions in pieces which they called Units. Units were sized so that 1 N represented 1% of the account equity.

> Thus, a unit for a given market or commodity can be calculated using the following formula:
> **Unit = 1% of Account / Market Dollar Volatility**
> or
> **Unit = 1% of Account / (N × Dollars per Point)**

(A = B = C; both formulas are fractions in the original.)

A second sentence also ties 1 N to 1% of equity. It is in Chapter 5 "Stops" → "Stop Placement" ([A] p.24, [B] p.23, [C] p.22; A = B = C):
> Since 1 N of price movement represented 1% of Account Equity, the maximum stop that would allow 2% risk would be 2 N of price movement.

Worked example ([A] p.17, [B] p.16; A = B). For Heating Oil the document gives "N = 0.0141", "Account Size = $1,000,000" and "Dollars per Point = 42,000 (42,000 gallon contracts with price quoted in dollars)". Unit Size = (0.01 × $1,000,000) / (0.0141 × 42,000) = 16.88, set as a fraction in the original. It then says:
> Since it isn’t possible to trade partial contracts, this would be truncated to an even 16 contracts.

> [B]: The Turtles were provided with a Unit size sheet on Monday of each week that listed the N, and the Unit size in contracts for each of the futures that we traded.

([A] reads "...that they traded.")

**Verdict:** matches the brief.

## 3. System 1 entry, the "last breakout" filter, and the failsafe
Section: Chapter 4 "Entries" → "Breakouts". [A] pp.20–21, [B] pp.19–20, [C] pp.18–19. Every quote here is identical in A, B and C.

> System 1 – A shorter-term system based on a 20-day breakout

> Turtles always traded at the breakout when it was exceeded during the day, and did not wait until the daily close or the open of the following day. In the case of opening gaps, the Turtles would enter positions on the open if a market opened through the price of the breakout.

> System 1 Entry - Turtles entered positions when the price exceeded by a single tick the high or low of the preceding 20 days. If the price exceeded the 20-day high, then the Turtles would buy one Unit to initiate a long position in the corresponding commodity. If the price dropped one tick below the low of the last 20-days, the Turtles would sell one Unit to initiate a short position.

> System 1 breakout entry signals would be ignored if the last breakout would have resulted in a winning trade. NOTE: For the purposes of this test, the last breakout was considered the last breakout in the particular commodity irrespective of whether or not that particular breakout was actually taken, or was skipped because of this rule. This breakout would be considered a losing breakout if the price subsequent to the date of the breakout moved 2N against the position before a profitable 10-day exit occurred.

> The direction of the last breakout was irrelevant to this rule. Thus, a losing long breakout or a losing short breakout would enable the subsequent new breakout to be taken as a valid entry, regardless of its direction (long or short).

> However, in the event that a System 1 entry breakout was skipped because the previous trade had been a winner, an entry would be made at the 55-day breakout to avoid missing major moves. This 55-day breakout was considered the Failsafe Breakout point.

**Verdict:** matches the brief. Three details worth keeping:
- The "last breakout" counts even if it was skipped, so it can be a hypothetical trade.
- The direction of the last breakout does not matter.
- The document's own term is "Failsafe Breakout point".

## 4. System 2 entry and the allocation between systems
Section: Chapter 4 "Entries", intro and "Breakouts". [A] pp.20–21, [B] pp.19–20, [C] pp.18–19.

The three System 2 quotes are identical in A, B and C:

> System 2 – A simpler long-term system based on a 55-day breakout.

> System 2 Entry - Entered when the price exceeded by a single tick the high or low of the preceding 55 days. If the price exceeded the 55 day high, then the Turtles would buy one Unit to initiate a long position in the corresponding commodity. If the price dropped one tick below the low of the last 55 days, the Turtles would sell one Unit to initiate a short position.

> All breakouts for System 2 would be taken whether the previous breakout had been a winner or not.

The allocation passage differs by edition:

> [B]/[C]: The Turtles were given rules for two different but related breakout systems we called System 1 and System 2. We were given full discretion to allocate as much of our equity to either system as we wanted. Some of us chose to trade all our equity using System 2, some chose to use a 50% System 1, 50% System 2 split, while others chose different mixes.

> [A]: The Turtles were given rules for two different but related breakout systems they called System 1 and System 2. They were given full discretion to allocate as much of their equity to either system as they wanted. Some chose to trade all their equity using System 2, some chose to use a 50% System 1, 50% System 2 split, while others chose different mixes.

**Verdict:** matches the brief. The allocation sentence exists; only its wording differs by edition.

## 5. Adding units and the maximum per market
Section: Chapter 4 → "Adding Units". [A] pp.21–22, [B] pp.20–21, [C] pp.19–20. Both quotes are identical in A, B and C.

> Turtles entered single Unit long positions at the breakouts and added to those positions at ½ N intervals following their initial entry. This ½ N interval was based on the actual fill price of the previous order. So if an initial breakout order slipped by ½ N, then the new order would be 1 full N past the breakout to account for the ½ N slippage, plus the normal ½ N unit add interval.

> This would continue right up to the maximum permitted number of units. If the market moved quickly enough it was possible to add the maximum four Units in a single day.

The document gives two examples:
- Gold, "N = 2.50", "55 day breakout = 310": units at 310.00, 311.25, 312.50 and 313.75.
- Crude Oil, "N = 1.20", "55 day breakout = 28.30": units at 28.30, 28.90, 29.50 and 30.10.

The per-market maximum is stated in Chapter 3 → "Units as a measure of Risk":
> Single Markets – A maximum of four Units per market.

**Verdict:** matches the brief. Read literally, the sentence says "single Unit long positions", and both examples are long trades.

## 6. Position limits
Section: Chapter 3 "Position Sizing" → "Units as a measure of Risk". [A] pp.17–18, [B] p.17, [C] p.16.

> [B]/[C]: The Turtles were given risk management rules that limited the number of Units that we could maintain at any given time, on four different levels. In essence, these rules controlled the total risk that a trader could carry, and these limits minimized losses during prolonged losing periods, as well as during extraordinary price movements.

([A] reads "...that they could maintain...")

> The limits were:

| Level | Type | Maximum Units |
|---|---|---|
| 1 | Single Market | 4 Units |
| 2 | Closely Correlated Markets | 6 Units |
| 3 | Loosely Correlated Markets | 10 Units |
| 4 | Single Direction – Long or Short | 12 Units |

(The table is identical in A, B and C.)

The text below the table is also identical in A, B and C:

> Single Markets – A maximum of four Units per market.

> Closely Correlated Markets – For markets that were closely correlated there could be a maximum of 6 Units in one particular direction (i.e.6 long units or 6 short units). Closely correlated markets include: heating oil and crude oil; gold and silver; Swiss franc and Deutschmark; TBill and Eurodollar, etc.

> Loosely Correlated Markets – For loosely correlated markets, there could be a maximum of 10 Units in one particular direction. Loosely correlated markets included: gold and copper; silver and copper, and many grain combinations that the Turtles did not trade because of positions limits.

> Single Direction – The maximum number of total Units in one direction long or short was 12 Units. Thus, one could theoretically have had 12 Units long and 12 Units short at the same time.

> The Turtles used the term loaded to represent having the maximum permitted number of Units for a given risk level. Thus, “loaded in yen” meant having the maximum 4 units of Japanese Yen contracts. Completely loaded meant having 12 Units. Etc.

Context from the same section (A = B = C):
> An example of an extraordinary price movement was the day after the October, 1987 stock market crash. The U.S. Federal Reserve lowered interest rates by several percentage points overnight to boost the confidence of the stock market and the country. The Turtles were loaded long in interest rate futures: Eurodollars, TBills and Bonds. The losses the following day were enormous. In some cases, 20% to 40% of account equity was lost in a single day. But these losses would have been correspondingly higher without the maximum position limits.

**Verdict:** matches the brief. For precision: the 6- and 10-unit limits apply "in one particular direction". The 12-unit cap is also per direction, so 12 units long and 12 short at the same time was theoretically possible.

## 7. Stops (2% risk, 2N) and the "non-negotiable" phrase
Section: Chapter 5 "Stops". The chapter intro is on [A] p.23, [B] p.22 and [C] p.21. "Turtle Stops" and "Stop Placement" are on [A] pp.23–24, [B] pp.22–23 and [C] pp.21–22.

**Phrase check: "These stops were non-negotiable exits … each time, every time, without fail." is FOUND, word for word, in all three builds.** It is in the subsection "Turtle Stops" ([A] p.24, [B] p.23, [C] p.22). The full text (A = B = C):
> These stops were non-negotiable exits. If a particular commodity traded at the stop price, then the position was exited; each time, every time, without fail.

The "no exceptions" sentence also exists, in the chapter intro before "Turtle Stops" (A = B = C):
> The most important thing about cutting your losses is to have predefined the point where you will get out, before you enter a position. If the market moves to your price, you must get out, no exceptions, every single time. Wavering from this method will eventually result in disaster.

Also in the chapter intro (A = B = C):
> Traders that don’t use stops go broke. The Turtles always used stops.

Stop placement (A = B = C):
> The Turtles placed their stops based on position risk. No trade could incur more than 2% risk.

> Since 1 N of price movement represented 1% of Account Equity, the maximum stop that would allow 2% risk would be 2 N of price movement. Turtle stops were set at 2 N below the entry for long positions, and 2 N above the entry for short positions.

> In order to keep total position risk at a minimum, if additional units were added, the stops for earlier units were raised by ½ N. This generally meant that all the stops for the entire position would be placed at 2 N from the most recently added unit. However, in cases where later units were placed at larger spacing either because of fast markets causing skid, or because of opening gaps, there would be differences in the stops.

The stops were prices the Turtles watched, not orders left with a broker:
> [B]/[C]: Having stops didn’t mean that the Turtles always had actual stop orders placed with the broker. Since the Turtles carried such large positions, we did not want to reveal our positions or our trading strategies by placing stop orders with brokers. Instead, we were encouraged to have a particular price, which when hit, would cause us to exit our positions using either limit orders, or market orders.

([A] is the same but uses "they/their/them".)

The alternate "Whipsaw" stop ([A] p.25, [B] p.24; A = B; not checked in C):
> Instead of taking a 2% risk on each trade, the stops were placed at ½ N for ½% account risk. If a given Unit was stopped out, the Unit would be re-entered if the market reached the original entry price. A few Turtles traded this method with good success.

**Verdict:** matches the brief, and the briefer's phrase is genuine. The ellipsis leaves out "If a particular commodity traded at the stop price, then the position was exited;".

## 8. Exits
Section: Chapter 6 "Exits" → "Turtle Exits" and "These are Difficult Exits". [A] p.28, [B] p.27, [C] p.26.

Both quotes are identical in A, B and C:

> The System 1 exit was a 10 day low for long positions and a 10 day high for short positions. All the Units in the position would be exited if the price went against the position for a 10 day breakout.
> The System 2 exit was a 20 day low for long positions and a 20 day high for short positions. All the Units in the position would be exited if the price went against the position for a 20 day breakout.

> For most traders, the Turtle System Exits were probably the single most difficult part of the Turtle System Rules. Waiting for a 10 or 20 day new low can often mean watching 20%, 40% even 100% of significant profits evaporate.
> There is a very strong tendency to want to exit earlier. It requires great discipline to watch your profits evaporate in order to hold onto your positions for the really big move. The ability to maintain discipline and stick to the rules during large winning trades is the hallmark of the experienced successful trader.

From the Chapter 6 intro ([A] p.27, [B] p.26, [C] p.25):
> [B]/[C]: Prices never go straight up; therefore it is necessary to let the prices go against you if you are going to ride a trend. Early in a trend this can often mean watching decent profits of 10% to 30% fade to a small loss. In the middle of a trend, it might mean watching a profit of 80% to 100% drop by 30% to 40%. The temptation to lighten the position to “lock in profits” can be very great.

([A] reads "...go straight up, therefore...")

**Verdict:** matches the brief. Note the hedging: "For most traders", "probably" and "can often mean".

## 9. Drawdown rule
Section: Chapter 3 "Position Sizing" → "Adjusting Trading Size". [A] p.19, [B] p.18, [C] p.17.

> [B]/[C]: The Turtles were instructed to decrease the size of the notional account by 20% each time we went down 10% of the original account. So if a Turtle trading a $1,000,000 account was ever was down 10%, or $100,000, we would then begin trading as if we had a $800,000 account until such time as we reached the yearly starting equity. If we lost another 10% (10% of $800,000 or $80,000 for a total loss of $180,000) we were to reduce the account size by another 20% for a notional account size of $640,000.

("was ever was" is in the original.)

> [A]: The Turtles were instructed to decrease the size of the notional account by 20% each time they went down 10% of the original account. So if a Turtle trading a $1,000,000 account size ever was down 10%, or $100,000, they would then begin trading as if they had a $800,000 account until such time as they reached the yearly starting equity. If they lost another 10% (10% of $800,000 or $80,000 for a total loss of $180,000) they were to reduce the account size by another 20% for a notional account size of $640,000.

> There are other, perhaps better strategies for reducing or increasing equity as the account goes up or down. These are simply the rules that the Turtles used.

(A = B = C)

The preceding paragraph, on notional accounts:
> [B]/[C]: The Turtles did not trade normal accounts with a running balance based on the initial equity. We were given notional accounts with a starting equity of zero and a specific account size. For example, many Turtles received a notional account size of $1,000,000 when we first started trading in February, 1983. This account size was then adjusted each year at the beginning of the year. It was adjusted up or down depending on the success of the trader as measured subjectively by Rich. The increase/decrease typically represented something close to the addition of the gains or losses that were made in the account during the preceding year.

> [A]: ... For example, most of the Turtles received a notional account size of $1,000,000 when they first started trading in February, 1983. ...

**Differs from the brief: "$900,000" appears nowhere in the document (NOT FOUND).** The example runs: $1,000,000 → down $100,000 → trade as if $800,000 → down another $80,000 (total loss $180,000) → $640,000. Actual equity after the first 10% loss would be $900,000, but the document never states that figure.

**An internal inconsistency to avoid repeating:** all editions say "February, 1983". That contradicts the document's own Introduction, where training ended "at the end of December, 1983", small accounts began "at the beginning of January", and funding came "at the start of February". By the document's own timeline, the funding month was February 1984.

## 10. "Most breakouts do not result in trends", "two or three trades", missed signals
(a) Chapter 6 "Exits", chapter intro before "Turtle Exits". [A] p.27, [B] p.26, [C] p.25. A = B = C:
> The Turtle System enters on breakouts. Most breakouts do not result in trends. This means that most of the trades that the Turtles made resulted in losses. If the winning trades did not earn enough on average to offset these losses, the Turtles would have lost money. Every profitable trading system has a different optimal exit point.

(b) Chapter 4 "Entries" → "Consistency". [A] p.22, [B] p.21, [C] p.20.
> The Turtles were told to be very consistent in taking entry signals, because most of the profits in a given year might come from only two or three large winning trades. If a signal was skipped or missed, this could greatly affect the returns for the year.

(A = B = C)

> [B]/[C]: The Turtles with the best trading records consistently applied the entry rules. The Turtles with the worst records, and all those who were dropped from the program, failed to consistently enter positions when the rules indicated.

([A] reads "...consistently applied their entry rules.")

(c) Chapter 7 "Tactics" → "Finally". [A] p.32, [B] p.31; not checked in C.
> [B]: The Turtle rules are very difficult to follow because they depend on capturing relatively infrequent large trends. As a result, many months can pass between winning periods; at times even a year or two.

> [A]: The Turtle rules are very difficult to follow because they depend on relatively infrequent large trends. Many months can pass between winning periods and losing periods, at times even a year or two.

**How the wording differs from the brief:**
- The document says "might come from", not "often come from".
- It says "most of the profits in a given year", not "a year's profits".
- It says "If a signal was skipped or missed, this could greatly affect the returns for the year", not "missing one signal can significantly affect" the results.
- These passages are in two different chapters: (a) is the Exits intro and (b) is Entries → Consistency.
- No sentence says "most trades are losers" in those words. The document says "most of the trades that the Turtles made resulted in losses".

## 11. Title page, author, date/version, free distribution
- **Cover** (PDF p.1, A and B): "Fighting the scams, frauds and charlatans" / "The Original Turtle Trading Rules".
- **Title page** (PDF p.2, A and B; checked on images): "ORIGINALTURTLES.ORG" / "The Original Turtle Trading Rules" / [Original Turtles logo] / "© 2003 OrignalTurtles.org". The misspelling "Orignal" is in the original.
- **Author:** no author name appears on the cover or title page. The Foreword is signed "Curtis Faith, an Original Turtle" ([A]/[B] p.5). The PDF metadata gives "Curtis M. Faith with help from many others" in [A] and "Curtis M. Faith" in [B].
- **Date/version:** the only date is "© 2003". **No version number or revision date appears in the text of either edition (NOT FOUND).** [A]'s file metadata says it was created 2003-04-09. When [B] was first created is UNVERIFIED; I only saw a 2013 re-render.
- **Statements about the rules being free** (Foreword; A = B unless noted):
  - "The Origin of the Free Rules Project" ([A]/[B] p.1): "This project had its seed in various discussions among a few of the original Turtles, Richard Dennis, and others regarding the sale of the Turtle Trading System rules by a former turtle, and subsequently, on a website by a non-trader. It culminated in this document, which discloses the Original Turtle Trading Rules in their entirety, free of charge."
  - A sidebar on the same page: "Richard Dennis and William Eckhardt were not consulted prior to the marketing of the Turtle Trading Rules and did not benefit in any way from the sale of the Turtle Rules they developed."
  - [B]: "Why? Because many of us believed that we owed an obligation to Richard Dennis not to reveal the rules, even after our contractual 10 year secrecy pact ended in late 1993. For this reason, we did not look kindly upon the sale of those rules by a former turtle."
  - [A]: "Why? Because many of the turtles believed that they owed an obligation to Richard Dennis not to reveal the rules even after their contractual 10 year secrecy pact ended in late 1993. For this reason, they did not look kindly upon the sale of those rules by a former turtle."
  - [A] only: "As one of the Original Turtles from the first Turtle class, I felt many of these same emotions."
  - "The Genesis of the Project" (p.4): "I had often thought that a great way to deal with this problem would be to give the Turtle Trading Rules away for free. Since others had already let the cat out of the bag, and since anyone who really wanted the rules could already get them by paying, it wouldn’t violate my sense of fair play to reveal them."
  - p.5: "While the rules are free, we respectfully ask that those who gain benefit from the rules and find them valuable send a donation supporting a charity in honor of Richard Dennis, Bill Eckhardt and the original Turtles. You can find a copy of the charities favored by the Turtles on the new web site: originalturtles.org."
  - **There is no explicit permission to copy or redistribute (NOT FOUND).** I searched both texts for distribut*, permission, reproduc* and copyright.
  - The Foreword names the website's co-founder as "Arthur Maddock".

## 12. Consistency and discipline; the Tactics chapter
**Consistency and discipline**
- Foreword → "Rules You Won’t Follow Don’t Matter" ([A]/[B] p.3; [A] checked on the page image):

  > [A]: What TurtleTrader.com and the Former Turtle don't tell you is that trading rules are only a small part of successful trading. The most important aspect of successful trading is confidence, consistency, and discipline.

  > [B]: ... The most important aspects of successful trading are confidence, consistency, and discipline.

- "The key is consistency and discipline" is **Richard Dennis's line, which Faith quotes from Jack Schwager's *Market Wizards***. It appears in the "Following Rules" sidebar on p.3 and again in "Finally": “I always say that you could publish my trading rules in the newspaper and no one would follow them. The key is consistency and discipline. Almost anybody can make up a list of rules that are 80% as good as what we taught our people. What they couldn’t do is give them the confidence to stick to those rules even when things are going bad.” – From Market Wizards, by Jack D. Schwager.
- Foreword p.4 (A = B): "On the whole, we had the confidence and the discipline to consistently apply the rules we were given. This was the secret of our success as traders."
- Chapter 1 ([A] p.8, [B] p.8, [C] p.7): [B]/[C] read "The confidence, consistency, and discipline afforded by a thoroughly tested mechanical system are the key to many of the most profitable traders’ success." [A] reads "...consistency and discipline ... is the key...".

**Tactics** (Chapter 7, [A] pp.29–32, [B] pp.28–31; not checked in C)

Summary of the chapter:
- Dennis and Eckhardt advised the Turtles to watch the market instead of leaving stop orders with a broker, and generally to prefer limit orders over market orders.
- In fast markets, don't panic: wait for the market to trade and stabilize.
- When many signals arrive at once, buy the strongest and short the weakest markets in a correlated group, entering one unit, in one contract month, per market at a time.
- Roll expiring contracts over a few weeks before expiry.

Short quotes:
> [B]: If the signals came all at once, we always bought the strongest markets and sold short the weakest markets in a group.

([A] reads "they always bought".)

> [B]: During these times, the Turtles were advised not to panic, and to wait for the market to trade and stabilize before placing their orders.

([A] has no comma after "panic".)

In "Entering Orders", [A] misspells the name as "William Eckardt"; [B] has "Eckhardt".

---

## Appendix (not requested): claims from the Introduction a history video may use
These come from Introduction → "The Turtle Experiment", [A]/[B] pp.6–7. The Introduction is not in [C]. **These are the document's claims; I did not verify them independently.**
- [A]: "In mid-1983 famous commodities speculator Richard Dennis was having an ongoing dispute with his long-time friend Bill Eckhardt about whether great traders were born or made." ([B] adds a comma after "mid-1983".)
- A = B: "They took out a large ad advertising positions for trading apprentices in Barron’s, the Wall Street Journal and the New York Times."
- [A]: "Since Rich was probably the most famous trader in the world at the time, he received over 1000 applicants. Of these he interviewed 80."
- [B]: "...he received submissions from over 1000 applicants. Of these, he interviewed 80."
- [A]: "This group was culled to 10, which became 13 after Rich added three people he already knew to the list. They were invited to Chicago and trained for two weeks at the end of December, 1983. They began trading small accounts at the beginning of January. After they proved themselves, Dennis funded most of the trainees with millions at the start of February."
- [B] (checked on the page image): "This group was culled to 10, which became 13 after Rich added three people he already knew to the list. We were invited to Chicago and trained for two weeks at the end of December, 1983, and began trading small accounts at the beginning of January. After we proved ourselves, Dennis funded most of us with $500,000 to $2,000,000 accounts at the start of February."
- [A]: "The Turtles became the most famous experiment in trading history because over the next four years, they earned an average annual compound rate of return of 80%." ([B] reads "we earned".)
- Chapter 2 (A = B): "In general, the Turtles traded all liquid U.S. markets except the grains and the meats."
