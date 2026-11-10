<?php
$pageTitle = 'Have Your Say on Public Spending | APET';
$pageDescription = 'Find your Australian representative, check public expenditure figures, and write a clear request with APET’s practical guide and editable letter template.';
include __DIR__ . '/includes/header.php';
?>
<link rel="stylesheet" href="/have-your-say.css">
<main class="container py-5 say-page" id="guide">
    <header class="say-intro mb-4">
        <p class="text-uppercase small fw-bold text-secondary">Evidence into participation</p>
        <h1 class="display-5 fw-bold">Have your say on public spending</h1>
        <p class="lead">Public money involves choices. Use the evidence on APET to ask questions, express your priorities, and request a clear response from your representatives.</p>
        <p>You may want spending reduced, increased, redirected, protected, or better explained. Your position is yours to decide. APET provides information and practical guidance without endorsing a party or policy.</p>
    </header>
    <nav class="say-steps mb-5" aria-label="Guide sections">
        <a href="#representative"><span>1</span> Find the right person</a>
        <a href="#evidence"><span>2</span> Check the evidence</a>
        <a href="#letter"><span>3</span> Write your request</a>
        <a href="#follow-up"><span>4</span> Follow up</a>
    </nav>

    <section id="representative" class="say-section" aria-labelledby="representative-title">
        <h2 id="representative-title">1. Find the right person</h2>
        <p>Start with the government responsible for the decision. Funding and service delivery can involve different governments; health and education often involve shared responsibilities. The <a href="https://peo.gov.au/understand-our-parliament/how-parliament-works/three-levels-of-government">Parliamentary Education Office explains the three levels of government</a>.</p>
        <div class="row g-3 my-2">
            <div class="col-lg-4"><div class="card h-100 shadow-sm"><div class="card-body p-4"><h3 class="h5">Federal</h3><p>For Australian Government spending, such as Medicare, defence, foreign aid and federal contracts, start with your federal MP. You can also contact a senator representing your state or territory.</p><a href="https://electorate.aec.gov.au/">Find your federal electorate (AEC)</a><br><a href="https://www.aph.gov.au/members/contact">Find an MP or senator’s contact details</a></div></div></div>
            <div class="col-lg-4"><div class="card h-100 shadow-sm"><div class="card-body p-4"><h3 class="h5">State or territory</h3><p>For matters such as public hospital services, public schools, police and state transport, contact a representative in your state or territory parliament.</p><a href="#directories">Choose your state or territory below</a></div></div></div>
            <div class="col-lg-4"><div class="card h-100 shadow-sm"><div class="card-body p-4"><h3 class="h5">Local council</h3><p>For council budgets, local roads, rubbish collection, parks and libraries, contact your councillor or the council. Use its official website for contact and consultation details.</p><a href="#directories">Find your council below</a></div></div></div>
        </div>
        <p class="small mt-3">A postcode can cover more than one federal electorate. Follow the AEC’s advice if your result is ambiguous. In the ACT, the Assembly and ACT Government also perform local government functions; Canberra has no separate council or mayor. <a href="https://www.parliament.act.gov.au/visit-and-learn/learn/resources/fs/levels-of-gov">Read the ACT explanation</a>.</p>
        <details id="directories" class="say-details my-4" open>
            <summary class="fw-semibold">State, territory and council directories</summary>
            <p class="mt-3">Use the member’s own listing to check their current contact method. Council links lead to government or local government association directories.</p>
            <div class="table-responsive"><table class="table align-middle say-directory">
                <caption>Official parliament links and council directories. Links reviewed 9 November 2026.</caption>
                <thead><tr><th scope="col">Where you live</th><th scope="col">Parliament</th><th scope="col">Local government</th></tr></thead>
                <tbody>
                    <tr><th scope="row">New South Wales</th><td><a href="https://www.parliament.nsw.gov.au/members-and-electorates">NSW members and electorates</a></td><td><a href="https://www.olg.nsw.gov.au/public/find-your-local-council">Find your NSW council</a></td></tr>
                    <tr><th scope="row">Victoria</th><td><a href="https://www.parliament.vic.gov.au/members/">Victorian members</a></td><td><a href="https://www.vic.gov.au/know-your-council">Find your Victorian council</a></td></tr>
                    <tr><th scope="row">Queensland</th><td><a href="https://www.parliament.qld.gov.au/Members/Current-Members">Queensland members</a></td><td><a href="https://www.dlgwv.qld.gov.au/local-government/for-the-community/local-government-directory">Queensland council directory</a></td></tr>
                    <tr><th scope="row">Western Australia</th><td><a href="https://www.parliament.wa.gov.au/Parliament/Memblist.nsf/MemberLookup/">Find your WA MP</a></td><td><a href="https://walga.asn.au/your-local-government/local-government-directory">WA council directory (WALGA)</a></td></tr>
                    <tr><th scope="row">South Australia</th><td><a href="https://www.parliament.sa.gov.au/Members/Members-Home">South Australian members</a></td><td><a href="https://www.localcouncils.sa.gov.au/map">Find your SA council</a></td></tr>
                    <tr><th scope="row">Tasmania</th><td><a href="https://www.parliament.tas.gov.au/contacts">Tasmanian member contact directories</a></td><td><a href="https://www.lgat.tas.gov.au/tasmanian-councils/find-your-local-council">Find your Tasmanian council (LGAT)</a></td></tr>
                    <tr><th scope="row">Northern Territory</th><td><a href="https://parliament.nt.gov.au/members">NT Assembly members</a></td><td><a href="https://infocomm.nt.gov.au/contact/public-sector-organisations">NT public bodies and council contacts</a></td></tr>
                    <tr><th scope="row">Australian Capital Territory</th><td><a href="https://www.parliament.act.gov.au/members/find">Find your ACT members</a></td><td>Contact your ACT representatives for local matters.</td></tr>
                </tbody>
            </table></div>
        </details>
        <p>If you are unsure who is responsible, ask the representative’s office to identify the relevant government or agency. For a routine service problem, the agency or council’s customer service team may be the best first contact. For a spending priority or policy change, explain your request to your elected representative.</p>
    </section>

    <section id="evidence" class="say-section" aria-labelledby="evidence-title">
        <h2 id="evidence-title">2. Check what the figures mean</h2>
        <p>A large amount alone does not establish waste or value for money. Consider what was delivered, who benefited, how results were measured and what alternatives were available.</p>
        <ul class="say-checklist">
            <li><strong>Amount and units:</strong> include the currency and whether the chart uses dollars, thousands, millions or billions.</li>
            <li><strong>Period and coverage:</strong> record the dates, location and programme. Check whether the number is annual, quarterly or a rolling 12-month total.</li>
            <li><strong>Type of figure:</strong> distinguish actual expenses or payments, budget estimates, forecasts, grant allocations and contract award values. A multiyear contract value is not annual spending.</li>
            <li><strong>Comparisons:</strong> check whether figures use the same definitions and account for inflation, population or service demand where relevant. Do not add overlapping periods or assume different APET datasets can be added without double counting.</li>
            <li><strong>Responsibility:</strong> a state label may describe a recipient’s location rather than the government paying. NDIS payments grouped by participant residence are not state-government expenditure totals.</li>
            <li><strong>Sources and limits:</strong> link the APET page and the original publisher. Read the source notes, including missing values and revisions. Separate your interpretation from what the data demonstrates.</li>
        </ul>
        <p>APET’s <a href="/transparency.php">transparency and methodology page</a> explains how its charts are produced.</p>
        <details class="say-details my-4">
            <summary class="fw-semibold">Prepare a figures-and-source note</summary>
            <p id="evidence-help" class="mt-3">Replace the brackets with the details from your chosen chart and its source notes. This worksheet does not automatically retrieve or verify figures. You can paste the completed note into your letter.</p>
            <label for="evidence-note" class="form-label fw-semibold">Your evidence note</label>
            <textarea id="evidence-note" class="form-control" rows="10" aria-describedby="evidence-help" spellcheck="true">Programme or subject: [name]
Amount and units: [amount in AUD; dollars/millions/billions]
Reporting period: [start and end dates]
Coverage: [location, programme, people or services included]
Type of figure: [payments / expenses / budget estimate / forecast / grant allocation / contract award]
Original publisher and source: [name and link]
APET page: [link]
Important limitations: [source notes, missing data or comparison limits]
Question I want answered: [your question]</textarea>
            <button type="button" class="btn btn-outline-dark mt-3" data-copy="evidence-note" hidden>Copy figures and source</button>
        </details>
    </section>

    <section id="letter" class="say-section" aria-labelledby="letter-title">
        <h2 id="letter-title">3. Write a clear, specific request</h2>
        <p>A useful starting point is a short email or one-page letter about one issue. Use your own words, explain why it matters to you, cite the evidence and ask for an action the recipient can take.</p>
        <ul>
            <li>Identify yourself as a local resident or constituent where applicable.</li>
            <li>Explain your priority respectfully and distinguish facts from your opinion.</li>
            <li>Ask for one concrete action: an explanation, a published evaluation, a review, a change in funding priorities, or a referral to the responsible minister.</li>
            <li>Request a written response and include a way to contact you. Use the office’s official form or email and provide any details it requires directly to that office.</li>
        </ul>
        <details class="say-details my-4"><summary class="fw-semibold">Examples of specific requests</summary><ul class="mt-3 mb-0"><li>“Please point me to the evaluation showing what this programme achieved.”</li><li>“Could you explain the reasons for the increase and whether the published figures are comparable?”</li><li>“Please ask the responsible minister to publish the performance measures and review timetable.”</li><li>“Please consider [my proposed funding priority] during the next budget process and explain your position.”</li></ul></details>
        <div class="card shadow-sm"><div class="card-body p-4">
            <h3 class="h4">Make this letter your own</h3>
            <p id="letter-help">Replace every bracketed prompt and review the figures before sending. Editing happens in your browser. APET does not receive or save your draft; copy or download it before leaving. Send it yourself using the recipient’s official contact details.</p>
            <label for="letter-draft" class="form-label fw-semibold">Editable letter</label>
            <textarea id="letter-draft" class="form-control" rows="19" aria-describedby="letter-help" spellcheck="true">Subject: Request about [programme or expenditure]

Dear [representative’s name],

I live in [suburb/electorate] and am writing about [programme or expenditure].

APET reports [amount and type of figure] for [reporting period and coverage], drawing on [original publisher and source link]. The APET page is [link].

My concern or priority is [explain your view in your own words and why it matters to you].

I would like you to [one specific action]. Could you explain how the results of this spending are assessed and what action you can take?

If this matter falls outside your responsibilities, please let me know which government or agency is responsible.

I would appreciate a written response.

Kind regards,
[Your name]
[Your preferred contact details]</textarea>
            <div class="d-flex flex-wrap gap-2 mt-3"><button type="button" class="btn btn-dark" data-copy="letter-draft" hidden>Copy my letter</button><button type="button" id="download-letter" class="btn btn-outline-dark" hidden>Download my letter (.txt)</button><button type="button" id="print-guide" class="btn btn-outline-dark" hidden>Print guide</button></div>
            <noscript><p class="mt-3 mb-0">You can edit the template and select its text to copy manually. Copy/download buttons need JavaScript. Use your browser’s print command to print the guide.</p></noscript>
            <p class="small mt-3 mb-0">Contacting a representative can contribute to public debate and scrutiny. It does not guarantee a reply or a policy change.</p>
        </div></div>
        <p id="action-status" class="say-status mt-3" role="status" aria-live="polite" aria-atomic="true"></p>
    </section>

    <section id="follow-up" class="say-section" aria-labelledby="follow-up-title">
        <h2 id="follow-up-title">4. Follow up and consider other routes</h2>
        <p>Keep your message, sources, date sent and any reference number. If you have not received a reply, a polite follow-up after two to four weeks is a reasonable starting point, unless the office gives a different timeframe. This is a suggestion, not an official response deadline.</p>
        <p>When a reply arrives, check whether it answers your question, identifies the responsible decision-maker and gives an action or timeframe. If it does not, ask one focused follow-up question. You can also request a meeting with your representative’s office.</p>
        <div class="row g-3 my-2">
            <div class="col-md-4"><h3 class="h5">Council consultations</h3><p>Look on your council’s website for its draft budget, annual plan and “Have your say” consultations. Check closing dates and any rules for submissions, public questions or speaking at meetings.</p></div>
            <div class="col-md-4"><h3 class="h5">Parliamentary inquiries</h3><p>If an inquiry covers your issue, a submission can put evidence and recommendations before a committee. Read its terms of reference, deadline and publication rules.</p><a href="https://www.aph.gov.au/Parliamentary_Business/Committees/Getting_Involved_in_Parliamentary_Committees">Federal committee participation</a></div>
            <div class="col-md-4"><h3 class="h5">Petitions</h3><p>A petition can ask a parliament or council for action within its responsibilities. Requirements differ. Federal House petitions must concern matters the House or Australian Government can act on.</p><a href="https://www.aph.gov.au/Parliamentary_Business/Petitions/House_of_Representatives_Petitions/Petition_Rules">Federal House petition rules</a></div>
        </div>
        <p class="small mt-3">Some submissions and petitions are published. Read the receiving organisation’s privacy and publication guidance before including personal information. State and territory parliaments provide their own inquiry and petition guidance through the directories above.</p>
    </section>
    <p class="small text-secondary border-top pt-3">Guide reviewed 9 November 2026. Official sources are linked throughout. For a broken link or factual correction, use <a href="https://github.com/auspublicexp/australian-public-expense-tracker/issues">APET’s issue tracker</a>; do not post your personal letter or contact details there.</p>
</main>
<script src="/js/have-your-say.js" defer></script>
<?php include __DIR__ . '/includes/footer.php'; ?>
