# LUCID

**Ask a question in plain English. Get a dashboard.**

LUCID (Language-to-Understanding Chart & Insight Dashboards) turns natural-language questions about a dataset of reported human-trafficking and related exploitation incidents into interactive, data-driven dashboards. You don't need to know SQL, write any code, or learn a query language — you type what you want to know, and LUCID builds the charts to answer it.

---

## ⚠️ A note on the subject matter

This tool works with data about human trafficking, forced labour, and related forms of exploitation. The topic is distressing by nature. The data describes *reported incidents* drawn from GDELT, anonymising any personal information.

---

## What LUCID is

LUCID is a natural-language-to-dashboard tool. Behind the scenes, a large language model reads your question and designs a response: it writes the database query needed to answer it and the chart specifications to display the result. The system then runs that query against the dataset, checks everything is valid and safe, and renders the dashboard in your browser.

LUCID was built as part of a master's dissertation. The dissertation aims to investigate the suitability of LLMs in generating structure visualisation grammars from natural language user queires. LUCID was developed by Jonathan Crocker for the MSc Data Science at the University of Edinburgh.

The code for the project can be found at: https://github.com/JonathanVeys/LUCID

---

## How to use it

1. **Type a question** into the search box in plain English.
2. **Submit it.** LUCID interprets your question, builds the queries and charts, and renders a dashboard.
3. **Explore the result** using the interactive charts (see *Reading your dashboard* below).
4. **Refine and ask again.** If the dashboard isn't quite what you wanted, rephrase your question and try once more.

### Example questions to try

- *"How many forced labour incidents were reported in Southeast Asia?"*
- *"Show how rates of pig butchering have changed over the last few years."*
- *"Which regions report the most sex trafficking?"*
- *"Compare the different crime types across Asian regions."*
- *"Give me an overview of trafficking in Europe."*

### Tips for better results

- **Be specific about what you want to compare or measure** — a crime type, a region, a time period, or a combination.
- **Mention time** ("over the last few years", "by year") when you want a trend.
- **Mention a place or category** to narrow the focus. LUCID understands regions and crime types even if your wording isn't exact — for example, "romance scams" is understood as pig butchering, and "Southeast Asian countries" as the Southeast Asia region.
- **One clear question works best.** A narrow question produces a single focused chart; a broad or open-ended one produces a multi-chart overview.

---

## Reading your dashboard

LUCID chooses one of two layouts depending on your question:

- **Focused** — a single, prominent chart for a specific question with one clear answer.
- **Informative** — several charts giving a broader, multi-angle overview for open-ended questions.

Each chart has a **title** and a short **summary** telling you what the chart is for and what to look for in it.

### Interacting with charts

Depending on the chart type, you can:

- **Hover** over any bar, line, or point to see the exact figures in a tooltip.
- **Click a legend entry** (on charts with multiple coloured series) to highlight that category and fade the rest.
- **Click a bar** to highlight it against the others.
- **Pan and zoom** on time-based and other continuous charts to inspect a particular period or range.

---

## When a question can't be answered

The dataset only contains certain kinds of information. If you ask something it simply doesn't cover — for example, *"What is the average age of victims?"* when age isn't recorded — LUCID will tell you plainly that it can't answer, and why, rather than inventing a misleading chart. If part of your question can be answered and part can't, it will answer the part it can.

---

## What the dataset contains

You can ask about incidents along these dimensions:

- **When** — the date an incident occurred and the date it was reported.
- **Where** — country and broad world region (e.g. Southeast Asia, East Africa, Europe, South America).
- **Type of crime** — including pig butchering, scam compounds, forced labour, sex trafficking, organ trafficking, debt bondage, and smuggling.
- **People involved** — number of victims, and the nationalities of victims and perpetrators where recorded.
- **Reporting confidence** — how reliable each record is judged to be (high, medium, or low).
- **Source** — the article each incident was drawn from.

The data source is current, but only covers a few previous years, so queries further back then that might not be possible.


---

## How it works (and why you can trust the numbers)

LUCID is designed so that the language model never sees the actual records. Its only job is to *design* the query and the charts — it then hands that design to the system, which runs it against the real database. This means:

- **Every number you see comes from the real data**, retrieved by a query, not generated or guessed by the model.
- **The model cannot fabricate findings.** Because it never reads the data, the chart summaries describe *what to look for*, not conclusions — the conclusions are yours to draw from the figures.
- **Queries are read-only and validated.** The system checks each query is safe and well-formed before it runs, and only ever reads data — it can never change it.
- **It corrects its own mistakes.** If the model's first attempt is invalid, the system feeds the errors back and asks it to try again before giving up.

LUCID is a research prototype and may occasionally produce imperfect results

---

## Important limitations

- **Reported incidents are not the full picture.** The figures reflect what has been *reported and recorded*, not the true scale of trafficking, which is widely under-reported. Higher counts in a region may reflect more reporting or media coverage rather than more crime.
- **The tool can make mistakes.** As an AI-assisted system, LUCID may occasionally misinterpret a question or choose a less-than-ideal chart. Rephrasing usually helps. Treat results as a starting point for exploration, not as authoritative statistics.
- **It can only answer what the data contains.** See *When a question can't be answered* above.

---

## Privacy and data handling

No data is collected when a user posts a question, this includes (but is not limited to) any information about the device, the question, or any metadata about the question.

---

## Feedback and contact

For any feedback or inquiries, please contact: s2090432@ed.ac.uk

---
