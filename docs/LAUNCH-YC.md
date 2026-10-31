# Coulis: taste-LLM launch and YC application draft

Working draft, 31 October 2026. No application or announcement has been submitted. Founder/team, incorporation, revenue, active-user and time-commitment answers require confirmation. The model is a research goal, not a released product.

## Company in one sentence

Coulis is a frontier research lab building a taste LLM that learns individual judgment, starting with writing, and makes it available as AI infrastructure.

## What changed

| Area | Previous infrastructure framing | Taste-LLM direction | Implication |
|---|---|---|---|
| Core technology | Memory, constraints and critique around existing models | A proposed language model that generates, critiques and chooses with personal taste | Model research becomes central; prototype becomes baseline/interface |
| Name | A layer that adds taste | Coulis as concentrated flavor that brings out character | Literal sauce imagery; avoid reducing the model to a cosmetic finishing pass |
| Product | Portable preference/checking layer | Model inference plus contextual taste state | Infrastructure remains the delivery layer |
| Research | Representation, retrieval and evaluation | Add model post-training, personalized generation and continual adaptation | Requires a technical owner, rights-cleared data, compute plan and controlled experiments |
| First buyer | AI products needing persistent preferences | AI writing/communication-agent products needing differentiated generation or evaluation | Must beat the equally informed base model at an acceptable inference cost |
| Launch | Research preview of local tools | Announce the lab and model research direction; release the local preview honestly | Do not call the preview a taste-LLM release |
| Competitive position | Complement to writing models | Direct overlap with writing-model developers, plus potential complementary API use | No longer claim “others write, we only judge” |

## Branding and website

Hero: **Taste infrastructure for AI. AI, with taste.**

Subheading: “Coulis is a frontier research lab building a taste LLM: a language model designed to generate, critique and choose with an understanding of individual judgment. Writing is our first domain.”

Primary CTA: Explore the research. Secondary: Try the prototype. Commercial CTA: Become a paid design partner → scoped integration/evaluation discussion; hosted model/API access is separately waitlisted. Be explicit that hosted inference and the taste LLM are not available today.

The literal coulis connection should appear in one strong visual and a short explanation. Use poured sauce ribbons, a spoon-drawn mark, berry/tomato reds and warm ceramic cream. Keep technical content precise. Do not turn the site into a food brand or force culinary names onto technical concepts.

## Step one for launch

Announce the lab and research hypothesis with an honest prototype demonstration. Before publication: review/merge the relevant PR, verify a fresh installation, record the approved preference/context loop, and publish the baseline protocol. None of these actions establishes a trained model or positive human outcome.

Recruit 1–2 paying AI product design partners and approximately ten consenting end users as initial targets, not claimed traction. Fundraise in parallel; do not wait for this pilot revenue to finance the model program. Separately establish permission for local service use, research evaluation and any future training. Run the native-model baseline study before choosing a training recipe.

### Announcement draft

“Introducing Coulis. A frontier research lab building a taste LLM.

Named for the sauce, built around a question: can AI learn what good means to you?

We’re starting with writing—what you keep, what you change, and what you leave out. Our goal is a model that can generate, critique and choose with an understanding of individual taste.

Today we’re sharing our research direction and an open-source local prototype for approved preference memory and draft checks. It is an experimental interface, not the trained model. We haven’t yet completed user outcome studies.

We’re opening discussions with AI product companies for paid design partnerships: integrate the current prototype, evaluate it with authorized users, and help shape the taste LLM. Hosted model access remains on the waitlist. We’re also raising venture capital to fund the research program.

Explore the research. Try the prototype. Build with Coulis.”

## YC application answers

These address common application topics; verify the current form and word limits before submission. Keep the research-lab identity but describe the actual technical objective concretely. [YC application guidance](https://www.ycombinator.com/howtoapply).

### Short description (under 50 characters)

A taste LLM that learns individual judgment

### What are you making?

We are building a language model that learns a person's editorial preferences and uses them to generate, critique and rank writing in context. We plan to serve it to AI writing and communication-agent products through an API. Our current open-source prototype uses existing models and approved preference memory; the Coulis taste LLM is not trained yet.

### What problem are you solving?

People repeatedly correct AI writing because fluent text can still make the wrong editorial choices for a particular person or audience. We want to learn from those choices and edits so an application can adapt what it generates and selects. Our research question is whether training for contextual personal judgment outperforms a general model supplied with the same writing samples and instructions.

### How far along are you?

We have a local Python/MCP prototype for approved contextual preferences, draft checks and critique using existing models. Its implementation has automated tests, but we have not completed user outcome studies. We have prepared a blinded baseline protocol. The next steps are permissioned data collection and evaluation, selection of a licensed base model, and a bounded training experiment. No proprietary taste-model checkpoint or hosted service is available today.

### What is technically new or difficult?

We are investigating person-conditioned judgment rather than only population-average writing preference. The difficult parts are learning from sparse and noisy edits, distinguishing durable taste from one-off decisions, applying preferences to new topics, adapting without forgetting, and measuring whether the actual person prefers the output. We have not yet established a novel method or performance advantage.

### How will you build the model?

We plan to begin with an appropriately licensed pretrained model, establish strong prompting and retrieval baselines, and test editorial supervised adaptation and preference optimization on specifically authorized data. We will compare generation, ranking and critique separately, and only promote a candidate after held-out human evaluation. Base-model choice, model scale, compute budget and training owner still need to be finalized. We are not claiming that foundation pretraining from scratch is necessary.

### Who are the customers?

Our intended first buyers are small AI writing and communication-agent product teams with existing users. They would pay for taste-conditioned generation, personalized evaluation or ranking, and preference-state updates if we demonstrate value over their current models. Professional writers and agencies are initial evaluation partners. Hosted access is currently waitlist only.

### How will you make money?

We are B2B2C: AI product companies pay Coulis, and their end users receive taste capabilities inside those products. We intend to charge from the first commercial engagement through upfront, scoped prototype integration and evaluation pilots. Later revenue would come from hosted taste-model/API usage and platform contracts. We are raising venture capital first to fund the research program while pursuing paid pilots in parallel. Pricing and unit economics are not yet validated. [Insert verified current revenue, if any; do not infer zero from absent data.]

### Who are your competitors?

Writing-focused language-model developers and native personalization in major models are direct competitors. Brand-voice platforms and taste-evaluation companies overlap with parts of the system. Our proposed distinction is learning an individual's contextual judgment, but we must demonstrate it against equally informed baselines. We do not assume that portability or calling the company a lab creates defensibility.

### Why did you choose this idea?

My work on founder and brand writing exposed how much editing is judgment: what fits this person, audience and moment. I want to learn from those repeated choices at the model level. [Replace this draft with one verified firsthand example, your exact role, and substantiated scope. Do not count agency revenue or clients as Coulis traction.]

### What is proprietary?

The current code is open source. We do not yet claim a trained proprietary model or an exclusive rights-cleared training corpus. Our intended defensibility is a better training/evaluation method, specifically permissioned contextual preference data and demonstrated model performance. Customers retain their writing and profile rights.

### Team / technical ownership / full-time commitment

[Name each founder, role, relevant technical/research work, code and model-training ownership, time committed, and any employment obligations. State AI-assisted development accurately. Do not invent a technical cofounder or imply that the current coding assistance is a research team.]

### Next milestone

Establish whether the current preference approach improves actual writer choices or editing effort against an equally informed base model. Then run a reproducible taste-model experiment with authorized training data and held-out topics/users. Secure a paid integration/evaluation partner for the current prototype while raising capital for the model experiment. Validate willingness to pay for hosted inference separately.

## SWOT

| Strengths | Weaknesses |
|---|---|
| Distinctive literal brand with a natural taste association | No trained taste LLM, original validated research result or completed user study yet |
| Concrete first domain with observable editorial choices | Technical research ownership, compute plan and data permissions need establishment |
| Existing local prototype can support baselines and feedback workflows | Sparse personal feedback may not support meaningful model adaptation |
| Model and API direction can serve multiple products | Training and inference introduce costs beyond the local tool |

| Opportunities | Threats |
|---|---|
| Personalized generation, evaluation and ranking for AI applications | Writing-focused and foundation models may offer sufficient native personalization |
| Permissioned longitudinal preference research | Model fine-tuning may fail to beat a good prompt/retrieval baseline |
| Distinctive evaluation based on actual writer judgment | Preference homogenization, forgetting, leakage and noisy labels |
| Model/API revenue if quality and economics are demonstrated | Research ambition can outrun team, data, compute or customer demand |

## YC investment viability

The taste-LLM direction makes Coulis more directly related to YC's “LLMs That Write Well” request, while raising the technical execution bar. It does not establish eligibility or predict admission. [YC Requests for Startups](https://www.ycombinator.com/rfs).

The investable claim to pursue: a capable team has found a specific weakness in existing models, can measure it, and can build a model improvement customers will pay for. Evidence needed: technical ownership; credible rights-cleared data access; a bounded experiment and compute budget; held-out model results; and integration demand. A stronger brand is helpful but is not a substitute for these.

Apply early with the actual state. YC explicitly accepts very early companies; waiting for revenue is not required. [YC FAQ](https://www.ycombinator.com/faq). No defensible admission probability can be inferred from these materials.

## Commercial and funding strategy

**B2B2C. VC-first. Paid from the first commercial engagement.** AI product companies are the buyers; their end users receive personalized taste capabilities. Raise venture capital for the model research and infrastructure while selling scoped integrations/evaluations of the existing prototype. These paid pilots are distinct from future hosted taste-LLM/API access, which remains waitlist only. No revenue or funding amount is claimed without verification. See [business model and initial paid offer](BUSINESS.md).
