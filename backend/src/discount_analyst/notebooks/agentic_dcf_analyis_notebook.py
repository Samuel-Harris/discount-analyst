import marimo

__generated_with = "0.18.3"
app = marimo.App(width="medium")


@app.cell
def _():
    from discount_analyst.dcf_analysis import DCFAnalysis, DCFAnalysisParameters
    from discount_analyst.assumption_maker import create_assumption_maker_agent
    from discount_analyst.data_fetcher import DataFetcher
    from discount_analyst.shared.ai_models_config import AIModelsConfig
    from discount_analyst.assumption_maker.user_prompt import create_user_prompt

    return (
        AIModelsConfig,
        DCFAnalysis,
        DCFAnalysisParameters,
        DataFetcher,
        create_assumption_maker_agent,
        create_user_prompt,
    )


@app.cell
def _():
    ticker = "DUO"
    return (ticker,)


@app.cell
def _(DataFetcher, ticker):
    data_fetcher = DataFetcher()
    stock_data = data_fetcher.fetch_stock_data(ticker=ticker)
    stock_data
    return


@app.cell
def _(AIModelsConfig):
    ai_models_config = AIModelsConfig()
    return (ai_models_config,)


@app.cell
def _():
    research_report = """
    # I. REVENUE GROWTH & QUALITY

    -   **High growth, slight deceleration:** Duolingo's revenue grew
        \~40--45% YoY in each 2024 quarter (Q1:\$167.6M +45%
        YoY[\[1\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208824000110/q1fy24pressrelease.htm#:~:text=Financial%20Measures%20Total%20revenues%20%28GAAP%29%24167%2C553%C2%A0%24115%2C661%C2%A045,2%2C582%29nm);
        Q2:\$178.3M +41%; Q3:\$192.6M +40%; Q4:\$209.6M
        +39%[\[2\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20revenues%20were%20%24209,of%20revenues)).
        Growth is moderating (45%→39% in Q4) but remains robust. Sequential
        (QoQ) growth is in the high single-digits each quarter. For example,
        Q4 2024 revenue was up 8.8% from Q3.
    -   **Strong bookings (ARR proxy):** Duolingo reports bookings (prepaid
        subscriptions) rather than ARR. FY2024 bookings were \$870.6M (+40%
        YoY)[\[2\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20revenues%20were%20%24209,of%20revenues),
        driven by +47% subscription bookings. (No explicit ARR metric is
        disclosed, but subscription bookings growth implies expanding
        recurring revenue).
    -   **Mostly recurring (subscription) revenue:** In Q4'24, 83% of
        revenue was subscription (recurring) and 17% "other" (ads, tests,
        in-app)[\[2\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20revenues%20were%20%24209,of%20revenues).
        Subscription revenue grew 48% YoY in Q4, versus only 5% growth in
        non-subscription
        revenue[\[2\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20revenues%20were%20%24209,of%20revenues).
        For FY2024, subscription accounted for \~81% of \$748.0M
        revenue[\[2\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20revenues%20were%20%24209,of%20revenues).
        This indicates high-quality recurring revenue.
    -   **No large customer dependency:** Duolingo's business is primarily
        B2C; it has no reported large customers. No single customer
        contributes \>10% of revenue (customer concentration is not
        disclosed). The user base is highly fragmented (millions of
        consumers and schools).
    -   **Geography:** Duolingo is global. In 2024, the U.S. accounted for
        \~\$312M (\~42%) of revenues, and international \~\$436M
        (58%)[\[3\]](https://sergeycyw.substack.com/p/duolingo-scaling-edtech-with-massive#:~:text=Total%20Addressable%20Market%20,leaving%20substantial%20room%20for%20expansion).
        US revenue grew \~31% YoY (312 vs 239M), while international grew
        \~74% (436 vs 250M), suggesting much faster growth overseas.
    -   **Customer segments:** Duolingo's core is consumer language
        learners; enterprise/SMB (Duolingo for Business/Schools) is minimal.
        No public split is given, but nearly all revenue comes from
        individual subscriptions. The fastest growth is in the
        consumer/subscriber base (paid subscribers \~9M end-2024, +\~50%
        YoY). (Duolingo does offer "Duolingo for Schools/Business," but this
        is a small portion of total revenue.)

    **Revenue Quality Assessment:** Revenue growth is high and largely
    subscription-based, indicating quality. Growth is broad-based globally
    with no big single-customer risk. The slight YoY deceleration is
    expected as the base grows. Overall, the revenue base appears robust and
    sticky (recurring subscriptions) with no obvious quality red flags.

      ---------------------------------------------------------------------------------
      Quarter   Q1 2023  Q2 2023  Q3 2023  Q4 2023  Q1 2024  Q2 2024  Q3 2024  Q4 2024
      --------- -------- -------- -------- -------- -------- -------- -------- --------
      Revenue   115.66   126.84   137.62   151.00   167.55   178.33   192.59   209.60
      (\$M)

      YoY       --       +9.6%    +8.5%    +9.7%    +44.8%   +40.6%   +39.9%   +39.0%
      Growth

      QoQ       --       +9.6%    +8.5%    +9.7%    +11.0%   +6.4%    +8.0%    +8.8%
      Growth
      ---------------------------------------------------------------------------------

    # II. PROFITABILITY & UNIT ECONOMICS

    -   **Gross margin stable but slight decline:** Duolingo's gross margin
        has been \~72--73%. For example, Q4 2024 gross margin was 71.9%
        (down \~1.2pp
        YoY)[\[4\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20gross%20margin%20decreased,a%20percentage%20of%20total%20revenue);
        FY2024 gross margin \~72.8% (down
        0.5pp)[\[4\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20gross%20margin%20decreased,a%20percentage%20of%20total%20revenue).
        The small decline is mainly due to higher AI hosting costs (Duolingo
        Max) and lower ad
        margins[\[4\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20gross%20margin%20decreased,a%20percentage%20of%20total%20revenue).
        These margins are on par with digital consumer subscription
        benchmarks (\~70--75%).
    -   **Operating profit expansion:** Duolingo is now GAAP-profitable each
        quarter. Q4 2024 GAAP operating expenses (R&D, S&M, G&A) as % of
        revenue improved YoY (GAAP R&D 32% vs 33% of rev, S&M 12% vs 13%,
        G&A 22% vs
        24%[\[5\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20GAAP%20R%26D%20expense,efficiently%20while%20delivering%20meaningful%20growth)).
        Q4 2024 net income was \$13.9M (net margin \~6.6%), compared to
        \$12.1M last year. Non-GAAP EBITDA margin is \~25% in recent
        quarters (e.g. Q4 adj. EBITDA
        \~25%[\[6\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=Net%20income%2412.1%2413.9%2015,153.6%24285.5%2086)).
        On a trailing 4-qtr basis, Rule-of-40 (40% growth + \~25% EBITDA
        margin ≈ 65) easily exceeds 40. Overall, Duolingo exhibits operating
        leverage: revenue growth is outpacing expense growth, driving
        expanding profitability.
    -   **Customer Acquisition/LTV:** Duolingo does not disclose CAC or LTV
        explicitly. Marketing spend is sizable (S&M \~12--13% of revenue)
        but has declined as a percent of sales, implying improved
        efficiency. Absent public metrics, we assume solid unit economics
        (given strong free cash flow).
    -   **CAC payback:** Not reported. Given that subscription ARPU is low
        (a few dollars/month) and customers stay for years, payback likely
        measured in 1--2 years, but specifics are undisclosed.
    -   **Rule of 40:** Currently well above 40. For FY2024: revenue growth
        \~41% + op. margin (\~25% adj.) ≈ 66, indicating strong combined
        growth+profitability.
    -   **Operating leverage:** Yes -- expense ratios are falling. For
        instance, FY2024 GAAP R&D was 31% of revenue vs 37% in
        FY2023[\[5\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20GAAP%20R%26D%20expense,efficiently%20while%20delivering%20meaningful%20growth).
        Non-GAAP R&D fell from 27% to 23% of
        revenue[\[5\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20GAAP%20R%26D%20expense,efficiently%20while%20delivering%20meaningful%20growth).
        Similar leverage is seen in S&M and
        G&A[\[5\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20GAAP%20R%26D%20expense,efficiently%20while%20delivering%20meaningful%20growth).
        This shows expenses rising slower than sales.

    **Conclusion:** Duolingo's unit economics are healthy. Gross margins are
    high and stable. The company is already GAAP-profitable and
    free-cash-flow positive, with operating leverage accelerating profits.
    While exact CAC/LTV data aren't public, the strong cash flow and
    improving expense ratios suggest sustainable unit economics.

      ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
      Metric         Q1 2024                                                                                                                                                                                                 Q2 2024        Q3 2024        Q4 2024
      -------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------- -------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
      Gross Margin   73.0%                                                                                                                                                                                                   73.4%          72.9%          71.9%[\[4\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20gross%20margin%20decreased,a%20percentage%20of%20total%20revenue)
      (%)

      Adj. EBITDA    26.3%[\[7\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208824000110/q1fy24pressrelease.htm#:~:text=%E2%80%A2Adjusted%20EBITDA%20was%20%2444,Adjusted%20EBITDA%20margin%2C%20respectively)   18.2%          24.7%          25.0%[\[6\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=Net%20income%2412.1%2413.9%2015,153.6%24285.5%2086)
      Margin (%)

      GAAP Net       16.1%                                                                                                                                                                                                   \~0%           12.1%          6.6%
      Margin (%)
      ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # III. MARKET OPPORTUNITY

    -   **TAM estimates:** Duolingo cites a huge market. One analysis pegs
        the *global edtech/digital learning TAM* at
        \~\$220 billion[\[3\]](https://sergeycyw.substack.com/p/duolingo-scaling-edtech-with-massive#:~:text=Total%20Addressable%20Market%20,leaving%20substantial%20room%20for%20expansion).
        The *language learning market* alone is \~\$61 billion (expected to
        grow to \~\$115B by
        2025)[\[8\]](https://sergeycyw.substack.com/p/duolingo-scaling-edtech-with-massive#:~:text=The%20global%20language%20learning%20market,is%20estimated%20at%20%24115%20billion).
        (This includes traditional and online language learning.) Other
        sources note \~1.5 billion people are learning a language
        worldwide[\[9\]](https://www.investing.com/analysis/duolingo-speaking-growth-fluently-despite-the-ai-noise-200670174#:~:text=Considering%20the%20total%20addressable%20market%2C,to%20learn%20a%20second%20language).
        Compared to these, Duolingo's 2024 revenue (\$748M) is only \~1.2%
        of the \$61B language market or \~0.3% of the broader edtech TAM,
        indicating vast remaining opportunity.
    -   **TAM growth/drivers:** The language learning market is growing
        fast. Online language learning is expected to grow at \~26% CAGR in
        the
        mid-2020s[\[8\]](https://sergeycyw.substack.com/p/duolingo-scaling-edtech-with-massive#:~:text=The%20global%20language%20learning%20market,is%20estimated%20at%20%24115%20billion).
        Global e-learning (all categories) is projected to grow \~17%
        annually[\[10\]](https://sergeycyw.substack.com/p/duolingo-scaling-edtech-with-massive#:~:text=The%20broader%20e,term%20potential%20through%20category%20diversification).
        Key drivers: globalization, immigration, travel demand, and rising
        consumer/enterprise education budgets. COVID-normalization has
        renewed demand for learning; AI/edtech advances (e.g. Duolingo Max)
        add growth tailwinds.
    -   **Current penetration:** With \~\$0.75B in revenue, Duolingo's share
        of the market is tiny. It has roughly 10 million paid subscribers
        out of \~1.5 billion learners (pay penetration
        \~0.7%)[\[9\]](https://www.investing.com/analysis/duolingo-speaking-growth-fluently-despite-the-ai-noise-200670174#:~:text=Considering%20the%20total%20addressable%20market%2C,to%20learn%20a%20second%20language).
        In other words, Duolingo is very early in penetration, with
        substantial room to grow its user base and ARPU.
    -   **Market share & competitors:** Duolingo is the clear market leader
        in consumer language apps. It claims roughly 60% of all language-app
        usage
        globally[\[11\]](https://market.us/report/language-learning-app-market/#:~:text=Approximately%2048,learning%20app%20activity%20in%202023).
        Main direct competitors are other app-based language platforms
        (Babbel, Rosetta Stone/Busuu, Mondly, Memrise, etc.), but none match
        Duolingo's scale or engagement. (By contrast, Chegg's Busuu reported
        only \~\$48M rev in
        2024[\[12\]](https://mlq.ai/stocks/DUOL/price-sales-ratio/#:~:text=Period%20Date%20P%2FS%20Ratio%20P%2FE,31%2063.89%20199.04%2014.72).)
        Duolingo's share by revenue is likely even higher since its ads and
        tests supplement the core app. The company has been growing much
        faster than any competitor, suggesting a rising share.
    -   **Expansion potential:** Duolingo is already expanding beyond core
        language learning: e.g. recent launches of math and chess courses
        (Duolingo
        Math/Chess)[\[13\]](https://www.nasdaq.com/press-release/duolingo-unveils-major-product-updates-turn-learning-real-world-power-duocon-2025#:~:text=Checkmate%2C%20Boredom%3A%20Duolingo%20Chess%20Gets,Social%20and%20Launches%20on%20Android),
        new Duolingo English Test features, and geographic rollout of
        Duolingo Max. These open adjacent markets (STEM, professional
        certification, etc.) and new geographies.
    -   **Market maturity:** The language learning market is still in
        early/mid growth stage given under-penetration and strong growth
        rates. The edtech sector broadly is high-growth. Thus there appears
        to be a long runway for multi-year growth at or near current rates.

    **Conclusion:** Duolingo's markets are very large and growing rapidly.
    Current revenue is only a fraction of TAM. The company is #1 in its
    space and has opportunities to expand into adjacent segments. This
    suggests significant runway remains for sustained growth.

    # IV. COMPETITIVE DYNAMICS

    -   **Top competitors:** Major direct competitors include Babbel
        (Europe's largest), Rosetta Stone (now part of Cambium/Busuu),
        Mondly, Memrise, and emerging free apps like LingoDeer. None come
        close to Duolingo's user base. According to industry data, Duolingo
        "captured around 60% of all language learning app activity in
        2023"[\[11\]](https://market.us/report/language-learning-app-market/#:~:text=Approximately%2048,learning%20app%20activity%20in%202023),
        dwarfing the next contenders. Market share (by usage) appears to be
        expanding in Duolingo's favor as it added millions of new users.
    -   **Big Tech threats:** Tech giants offer translation tools (e.g.
        Google Translate, Apple Live Translation) but these serve a
        different need (instant translation vs. learning). No FAANG company
        currently offers a comprehensive gamified language-learning
        platform. Microsoft/AI companies could potentially integrate
        learning, but Duolingo's moat is engagement (game-like experience)
        which big players may find hard to replicate quickly. Overall,
        big-tech threat is moderate -- more relevant for casual translators,
        less for committed learners.
    -   **Emerging startups:** Aside from established apps, few startups
        have deep pockets in language learning. Some venture-funded apps
        exist (e.g. Lingvist, Tandem), but none have disrupted Duolingo's
        position. No new entrant is reported to be gaining major traction
        against Duolingo.
    -   **Win rates:** Duolingo does not publicize competitive win/loss
        rates. However, user metrics (DAUs up \>50% YoY) and share gains
        suggest Duolingo is winning share. Its freemium model attracts a
        large funnel, and a high percentage convert to paid over time.
    -   **Market share trajectory:** Likely gaining. Duolingo's rapid user
        growth and market leadership imply it is taking share from smaller
        apps and traditional learning methods.
    -   **Pricing power:** Duolingo has been able to raise prices modestly
        (family plans and new "Max" tier) without hurting subscription
        growth. Management notes that average revenue per subscriber (ARPU)
        rose \~2% YoY in Q4 due to mix and price
        increases[\[14\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=The%20increase%20in%20both%20subscription,plan%20and%20Duolingo%20Max%20subscribers).
        This indicates some ability to increase pricing, aided by unique AI
        features (Max) and family plans. Churn remains low, so it appears to
        have pricing power at the premium end.

    **Conclusion:** Duolingo enjoys a strong competitive position. It
    dominates the consumer language-app market, with no equal rival in
    scale. Competitive threats seem manageable. The company's brand,
    engagement features, and continuing innovation (e.g. Max) give it a
    defendable position against incumbents and any new entrants.

    # V. PRODUCT & TECHNOLOGY

    -   **Product-market fit:** Duolingo's extremely high usage indicates
        great fit. It reports \~103 million MAUs with 32% engaging
        daily[\[15\]](https://sergeycyw.substack.com/p/duolingo-scaling-edtech-with-massive#:~:text=User%20engagement%20is%20a%20standout,in).
        App reviews are overwhelmingly positive (e.g. millions of 5-star
        ratings on app stores). Independent sources (e.g. app rankings,
        EdTech reviews) consistently list Duolingo as a top learning app.
        User testimonials often praise its game-like learning.
    -   **Mission-critical vs. nice-to-have:** Duolingo is generally
        "nice-to-have" in the sense that it is consumer/education spending
        (vs. essential IT). However, for committed learners (students,
        professionals), it can become habit-forming and valued. Adoption in
        schools (free mode) also suggests educators see it as useful, but
        not mission-critical like core school software.
    -   **Product differentiation:** Key advantages include: a highly
        gamified and engaging UX (streaks, rewards, social features); large
        free-user funnel enabling network effects; constant feature
        innovation (Duolingo Max with AI tutor, personalized exercises, new
        content types); and strong branding (owl mascot). The "Max" tier is
        a unique product with AI-driven live tutoring (via Duolingo's Lily
        chatbot and Video Call) that competitors
        lack[\[16\]](https://www.nasdaq.com/press-release/duolingo-unveils-major-product-updates-turn-learning-real-world-power-duocon-2025#:~:text=Duolingo%20also%20highlighted%20two%20powerful,scale%20experimentation).
        The ability to learn multiple subjects (languages, math, chess,
        music) in one app also differentiates Duolingo as a broader learning
        platform.
    -   **R&D spend:** Duolingo invests heavily in R&D. In Q4 2024, GAAP R&D
        was 32% of revenue (down from 33% in
        Q4'23)[\[5\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20GAAP%20R%26D%20expense,efficiently%20while%20delivering%20meaningful%20growth).
        Non-GAAP (ex-SBC) R&D was 23% of revenue in Q4 (vs 24%
        prior)[\[5\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20GAAP%20R%26D%20expense,efficiently%20while%20delivering%20meaningful%20growth).
        This remains high by SaaS standards, reflecting ongoing product
        development. Over FY2024, GAAP R&D averaged \~31% of rev (vs 37% in
        FY2023)[\[5\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20GAAP%20R%26D%20expense,efficiently%20while%20delivering%20meaningful%20growth)
        -- showing investment, but also leveraging growth.
    -   **Innovation pipeline:** Duolingo regularly launches new features.
        Recent highlights include *Duolingo Max* (AI-powered features like
        GPT-based explanations and Video Calls) and *family/shared plans*
        (higher price
        tiers)[\[14\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=The%20increase%20in%20both%20subscription,plan%20and%20Duolingo%20Max%20subscribers).
        The Duocon 2025 announcements added LinkedIn integration of Duolingo
        Scores and expanded Duolingo Chess (Android release, PvP
        mode)[\[17\]](https://www.nasdaq.com/press-release/duolingo-unveils-major-product-updates-turn-learning-real-world-power-duocon-2025#:~:text=For%20the%20first%20time%20ever%2C,the%20world%E2%80%99s%20largest%20professional%20network)[\[18\]](https://www.nasdaq.com/press-release/duolingo-unveils-major-product-updates-turn-learning-real-world-power-duocon-2025#:~:text=,with%20Android%20support%20to%20follow).
        Behind the scenes, the company runs extensive A/B testing and has an
        AI/ML team (e.g. next-word prediction, personalized lessons).
        Roadmaps mention continued expansion of Max to all courses and new
        subjects (e.g. more math lessons, literacy). Thus, the pipeline
        appears active.
    -   **Technology stack:** Duolingo is a modern cloud-native mobile/web
        app. It runs on AWS/GCP infrastructure, uses machine learning (now
        generative AI) for personalization, and has native apps on
        iOS/Android/Web. It frequently updates its apps. There is no sign of
        outdated legacy tech; rather, it invests in cutting-edge AI research
        (see Duolingo Max features) and agile development.
    -   **Partnerships/integrations:** Duolingo has begun integrating into
        larger ecosystems. For example, Duocon 2025 announced Duolingo Score
        integration with
        LinkedIn[\[17\]](https://www.nasdaq.com/press-release/duolingo-unveils-major-product-updates-turn-learning-real-world-power-duocon-2025#:~:text=For%20the%20first%20time%20ever%2C,the%20world%E2%80%99s%20largest%20professional%20network),
        allowing learners to showcase skills. It supports single sign-on
        (Google/Apple) and has a "Duolingo for Schools" portal. While not
        deeply embedded in enterprise systems (like Salesforce), it does
        integrate with education ecosystems (Google Classroom through
        Duolingo for Schools, Alexa/voice assistants, etc.). Further
        partnership potential exists (e.g. enterprise language training
        programs).
    -   **Platform potential:** Duolingo is evolving beyond a single course
        app. With multiple learning categories (languages, math, music,
        chess) and advanced features (AI tutor, social learning), it could
        become an education "platform" spanning K-12 and adult learning
        niches. Its large user data could be leveraged to launch new
        products (e.g. placement tests, certifications). The move to
        integrate scores with LinkedIn suggests a vision of Duolingo
        credentials being recognized in academia/professional settings,
        which would widen its platform role.

    **Conclusion:** Duolingo's product is highly differentiated and
    well-received. Continuous innovation (AI-powered tutoring, new subjects,
    gamification) and strong user engagement (DAUs/MAUs) indicate defensible
    product/market fit. The investment in R&D and AI suggests it has the
    capability to sustain and deepen its advantage. The product appears
    sticky (habit-forming) rather than easily replaced.

    # VI. CUSTOMER METRICS

    -   **Retention (NRR):** As a consumer/subscription service, traditional
        "net dollar retention" is not reported. However, growth of average
        revenue and subscriber counts suggests strong retention and
        expansion via upsells (family plans, Max). We assume NRR is \>100%
        (users often upgrade to premium or higher tiers). (Exact NRR is not
        disclosed.)
    -   **Churn:** Specific churn rates are not disclosed. Duolingo's
        business model (monthly subscriptions) implies some churn, but the
        growth in subscribers (\~+50% YoY) and rising
        ARPU[\[14\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=The%20increase%20in%20both%20subscription,plan%20and%20Duolingo%20Max%20subscribers)
        imply net retention is positive. Given high engagement (daily use),
        customer churn is likely below typical SaaS benchmarks, but no
        public numbers exist.
    -   **Customer growth:** Paid subscribers are growing \~50% YoY. E.g.,
        8.0M at Q2'24 (vs 5.2M in Q2'23, +52%); 8.6M at Q3'24 (+47% YoY).
        (Independent sources report \~9.5M by end-2024). Free user MAUs are
        also growing strongly (DAUs +54% YoY in
        Q2/Q3'24[\[19\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208824000110/q1fy24pressrelease.htm#:~:text=%E2%80%A2Daily%20active%20users%20,from%20the%20prior%20year%20quarter)).
        New subscriber additions each quarter remain in the millions.
    -   **ACV/ARPU trend:** Duolingo reports subscription revenue per
        average subscriber. In Q4 2024, ARPU rose \~2%
        YoY[\[14\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=The%20increase%20in%20both%20subscription,plan%20and%20Duolingo%20Max%20subscribers),
        due to more premium-tier (Family/Max) users. This marks the first
        annual ARPU increase since 2017. (Exact ARPU wasn't given, but this
        indicates a modest upward trend.) ACV (for institutional deals) is
        not disclosed, as enterprise sales are small.
    -   **Gross Retention (GRR):** Not reported. With a consumer base,
        expansions (family, Max) likely drive net revenue retention above
        100%. Base-user retention (ignoring upsell) is unknown, but the
        engagement model (streaks, free content) aims to keep free users
        active.
    -   **Cohorts:** Public disclosures do not include cohort-level metrics.
        Anecdotally, Duolingo emphasizes user engagement improvements (e.g.
        new lesson types, AI coaching), which suggests older cohorts
        continue to use and expand (via adding courses or features).

    **Conclusion:** Key user metrics are strong. Paid subscribers and daily
    active users are accelerating, and indications are that existing
    customers are not churning significantly. ARPU is beginning to tick up
    with new products, which should improve customer economics over time.
    Overall, customers appear to be retaining and extracting more value from
    the product.

    # VII. MANAGEMENT & EXECUTION

    -   **Leadership quality:** Co-founder Luis von Ahn (CEO) and co-founder
        Severin Hacker (CTO) remain in control. Von Ahn has a strong tech
        pedigree (reCAPTCHA, CAPTCHA patents sold to Google) and has led
        Duolingo since its founding. Other executives (new CFO Matt Skaruppa
        in 2024, long-tenured CMO/Y Chang, etc.) have relevant experience.
        The team has delivered consistent execution (product launches, rapid
        scaling).
    -   **Founder-led:** Yes. Von Ahn and Hacker co-founded Duolingo at CMU
        in 2011 and maintain leadership. Founder ownership is significant
        via long-term equity awards. In fact, **\~15% of Q4 SBC** was
        pre-IPO founder
        equity[\[20\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=for%20stock,for%20our%20founders%20through%202031),
        which vest through 2031, indicating founders have substantial
        incentive to grow the company. This suggests alignment with
        shareholders.
    -   **Insider equity:** Founders and executives hold a meaningful stake
        (see above), and there are no signs of large stock sales by
        management beyond planned vesting. Long vesting schedules (founder
        awards through
        2031[\[20\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=for%20stock,for%20our%20founders%20through%202031))
        show management's "skin in the game."
    -   **Guidance track record:** Duolingo generally meets or beats its own
        guidance. For example, Q4 2024 revenue came in at
        \$209.6M[\[2\]](https://www.sec.gov/Archives/edgar/data/1562088/000156208825000039/q4fy24duolingo12-31x24shar.htm#:~:text=In%20Q4%2C%20revenues%20were%20%24209,of%20revenues),
        above the high end of guidance (\$205.5M) set in Q3. Management is
        cautious yet often conservative on the low end of guidance ranges,
        then executes toward the top (as seen in late 2024). No notable big
        misses have been reported.
    -   **Capital allocation:** Duolingo has been capital-light. It has made
        no material M&A deals or share buybacks to date. Cash flow has been
        reinvested in product and marketing. Balance sheet shows negligible
        debt (see next section). No major capital-return programs have been
        announced.
    -   **Turnover:** Executive turnover has been low. The CEO and founders
        have stayed; the only notable change was hiring a full-time CFO in
        2024 (previously an interim). No mass departures or leadership
        changes have been reported.
    -   **Communication:** Management provides detailed shareholder letters
        and conference calls. They acknowledge both achievements and
        challenges (e.g. they have openly discussed AI competition and
        guideline changes). Recent communications (e.g. Q4 letter) have been
        transparent about costs (AI in cost of revenue) and realistic on
        growth. Overall, communication appears straightforward and
        data-backed.
    -   **Board:** The board includes experienced tech and business leaders
        (e.g. Bonnie Ross, veteran game industry exec, joined in Dec
        2024[\[21\]](http://investors.duolingo.com/news-releases/news-release-details/gaming-industry-visionary-bonnie-ross-joins-duolingo-board#:~:text=Gaming%20Industry%20Visionary%20Bonnie%20Ross,as%20an%20independent
    """.strip()
    return (research_report,)


@app.cell
def _(research_report):
    print("\n".join(research_report.splitlines()[:5]))
    return


@app.cell
async def _(
    ai_models_config,
    create_assumption_maker_agent,
    create_user_prompt,
    research_report,
    ticker,
):
    assumption_maker_agent = create_assumption_maker_agent()

    async with assumption_maker_agent.run_stream(
        create_user_prompt(ticker=ticker, research_report=research_report),
        usage_limits=ai_models_config.assumption_maker.usage_limits,
    ) as result:
        # Optionally process streaming events
        async for message in result.stream_output():
            print(f"Streaming: {message}")

    agent_output = await result.get_output()
    return (agent_output,)


@app.cell
def _(agent_output):
    agent_output
    return


@app.cell
def _(agent_output):
    print(agent_output.stock_assumptions.reasoning)
    return


@app.cell
def _(DCFAnalysis, DCFAnalysisParameters, agent_output):
    dcf_analyis_parameters = DCFAnalysisParameters(
        stock_data=agent_output.stock_data,
        stock_assumptions=agent_output.stock_assumptions,
        risk_free_rate=0.0397,
    )
    dcf_analyis = DCFAnalysis(dcf_analysis_params=dcf_analyis_parameters)
    dcf_analysis_result = dcf_analyis.dcf_analysis()
    dcf_analysis_result
    return (dcf_analysis_result,)


@app.cell
def _(dcf_analysis_result, ticker):
    print(
        f"Intrinsic share value of {ticker} according to AI: ${dcf_analysis_result.intrinsic_share_price}"
    )
    return


if __name__ == "__main__":
    app.run()
