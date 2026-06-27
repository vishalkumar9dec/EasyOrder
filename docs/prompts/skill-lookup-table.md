# Skill Lookup Table — Complete Reference

Use this table to find the right skill for any task. Organized by workflow phase, from idea to production.

> **How to use:** Find your task in the "I want to..." column → use the skill in the "Skill" column → adapt the prompt pattern.  
> **Rule:** Don't ask the agent "which skill should I use?" — find it here.

---

## Phase 0: Ideation & Validation

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Stress-test a plan before building | `/grill-me` | `Analyze X, /grill-me on my plan` | Relentless interview — pokes holes in your assumptions |
| Stress-test AND create docs as we go | `/grill-with-docs` | `/grill-with-docs on my architecture` | Same grilling but also produces ADRs and glossary entries |
| Explore an idea through teaching | `/teach` | `Teach me about X` | Teaches you a concept within your workspace context |

---

## Phase 1: Product Requirements

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Write a PRD from raw product doc | `/to-prd` | `Create a PRD using /to-prd from @[docs/product-doc.md]` | Synthesizes conversation/doc into structured PRD |
| Break PRD into GitHub issues | `/to-issues` | `Break @[docs/prd.md] into issues using /to-issues` | Converts PRD stories into individual trackable issues |
| Write a QA session / file bugs | `/qa` | `Start a QA session` | Interactive bug reporting → GitHub issues |

---

## Phase 2: Tech Stack & Decisions

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Document tech stack decisions | `/decision-mapping` | `Use /decision-mapping to document choices for X` | Creates investigation tickets, drives each to a resolution |
| Build domain glossary (CONTEXT.md) | `/domain-modeling` | `Build domain model for X` | Pins down ubiquitous language, bounded contexts |
| Build domain glossary (alternative) | `/ubiquitous-language` | `Define ubiquitous language for X` | Similar to domain-modeling, focused on terminology |

---

## Phase 3: Architecture & System Design

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Design deep modules with testing seams | `/codebase-design` | `Design deep modules for X using /codebase-design` | Module interfaces, Protocol types, seam design |
| Compare 2+ interface alternatives | `/design-an-interface` | `Design it twice for X` | Generates radically different designs via parallel sub-agents |
| Improve existing architecture | `/improve-codebase-architecture` | `Improve the architecture of X` | Refactors existing code structure |
| Create implementation plan & tasks | **Built-in planning mode** | `Create an implementation plan for X` | Agent creates `implementation_plan.md` + `task.md` automatically |
| Generate professional PNG diagrams | `generate_image` | `Generate .png diagram of X with [constraints]` | Panel-based, color-coded architecture diagrams |
| Create call flow sequence diagrams | *(manual Mermaid)* | `Create sequenceDiagram for each use case in PRD` | Technical sequence diagrams in `.md` files |

---

## Phase 4: Review & Quality

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Review code/docs against PRD | `/review` | `Review @[docs/hld.md] against @[docs/prd.md]` | Standards + Spec compliance, parallel sub-agents |
| Audit Firestore security rules | `firebase-security-rules-auditor` | `Audit the security rules in firestore.rules` | Evaluates rules for vulnerabilities |
| Review UI against web guidelines | `/web-design-guidelines` | `Review my UI against best practices` | Checks accessibility, UX, design patterns |
| Review docs/prose for writing style | `/writing-guidelines` | `Review my docs for writing style` | Voice, tone, clarity checks |

---

## Phase 5: Implementation

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Implement feature via saved plan | `/implement` | `Implement X based on @[docs/prd.md]` | Executes implementation from PRD or issues |
| Build feature test-first (TDD) | `/tdd` | `Implement X using /tdd (red-green-refactor)` | Write test → make it pass → refactor |
| Build an MCP server | `/mcp-builder` | `Build an MCP server for X` | FastMCP (Python) or MCP SDK (Node) server |
| Build a rapid UI prototype | `/prototype` | `Prototype the X screen` | Quick throwaway UI to validate ideas |
| Build or style UI components | `/frontend-design` | `Design the PWA layout using /frontend-design` | Aesthetic direction, typography, visual identity |
| Create visual art / posters | `/canvas-design` | `Create a poster for X` | Beautiful static visual designs as PNG/PDF |
| Style artifacts with a theme | `/theme-factory` | `Apply a theme to X` | 10 pre-set themes or generate custom ones |

---

## Phase 6: Frontend-Specific

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Optimize React/Next.js performance | `vercel-react-best-practices` | `Optimize this React component` | Bundle optimization, data fetching patterns |
| Fix React composition / prop drilling | `vercel-composition-patterns` | `Refactor X using composition patterns` | Compound components, render props, context |
| Add view transitions / animations | `vercel-react-view-transitions` | `Add page transitions to X` | React View Transition API |
| Build React Native mobile app | `vercel-react-native-skills` | `Build a React Native component for X` | Expo, native modules, mobile performance |
| Build complex HTML artifacts | `/web-artifacts-builder` | `Build a multi-component artifact for X` | React + Tailwind + shadcn/ui artifacts |
| Check modern web API best practices | `modern-web-guidance` | *(auto-triggers on HTML/CSS/JS tasks)* | Searches web.dev for current patterns |
| Build a Chrome extension | `chrome-extensions` | `Create a Chrome extension for X` | Manifest V3, service workers, Chrome APIs |

---

## Phase 7: Testing & Debugging

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Debug a broken feature | `/diagnosing-bugs` | `Diagnose why X is failing` | Structured diagnosis loop for hard bugs |
| Test a web app via browser automation | `/webapp-testing` | `Test the login flow of my app` | Playwright-based frontend testing |
| Automate browser interactions | `/agent-browser` | `Open the website and click X` | Full browser automation CLI |
| Debug via Chrome DevTools | `chrome-devtools` | `Debug the network requests on X page` | Performance, network, console inspection |
| Fix accessibility issues | `a11y-debugging` | `Audit accessibility of X` | ARIA, focus, keyboard nav, contrast |
| Diagnose memory leaks | `memory-leak-debugging` | `Diagnose memory leak in X` | Heap snapshots, memlab analysis |
| Optimize page load (LCP) | `debug-optimize-lcp` | `Why is my page load slow?` | Largest Contentful Paint debugging |
| Plan a safe refactoring | `/request-refactor-plan` | `Plan a refactor for X` | Tiny-commit refactor RFC → GitHub issue |

---

## Phase 8: Deployment & Ops

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Deploy to Vercel | `/deploy-to-vercel` | `Deploy and give me the link` | Vercel deployment with preview URLs |
| Deploy with Vercel CLI tokens | `vercel-cli-with-tokens` | `Deploy using Vercel token` | Token-based auth (CI/CD friendly) |
| Optimize Vercel costs | `vercel-optimize` | `Reduce my Vercel bill` | Cost/performance optimization, caching |
| Set up pre-commit hooks | `/setup-pre-commit` | `Add pre-commit hooks with Husky` | Prettier, type-check, tests on commit |
| Resolve git merge conflicts | `/resolving-merge-conflicts` | `Resolve the merge conflict` | Interactive conflict resolution |
| Block dangerous git commands | `git-guardrails-claude-code` | `Add git safety hooks` | Blocks push, reset --hard, clean, etc. |

---

## Phase 9: Firebase-Specific

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Set up Firebase project | `firebase-basics` | `Initialize Firebase for this project` | CLI setup, auth, project config |
| Set up Firestore database | `firebase-firestore` | `Create Firestore collections for X` | Schema design, security rules, queries |
| Add Firebase Authentication | `firebase-auth-basics` | `Add Google sign-in to my app` | Auth flows, user management |
| Deploy static site to Firebase | `firebase-hosting-basics` | `Deploy to Firebase Hosting` | Static/SPA hosting (not App Hosting) |
| Deploy Next.js to Firebase | `firebase-app-hosting-basics` | `Deploy my Next.js app` | App Hosting for SSR frameworks |
| Add Gemini AI via Firebase | `firebase-ai-logic-basics` | `Add Gemini to my Firebase app` | Firebase AI Logic integration |
| Audit Firestore security rules | `firebase-security-rules-auditor` | `Audit my Firestore rules` | Security evaluation |

---

## Document & File Operations

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Create/edit Word documents | `/docx` | `Create a Word doc for X` | .docx creation, editing, formatting |
| Create/edit PowerPoint decks | `/pptx` | `Create a slide deck for X` | .pptx creation, layouts, speaker notes |
| Create/edit spreadsheets | `/xlsx` | `Create a spreadsheet for X` | .xlsx creation, formulas, charting |
| Create/edit PDFs | `/pdf` | `Create a PDF report for X` | PDF creation, merging, splitting, OCR |
| Write internal communications | `/internal-comms` | `Write a status report for X` | Status reports, leadership updates, FAQs |
| Co-author documentation | `/doc-coauthoring` | `Help me write the technical spec for X` | Structured doc co-authoring workflow |
| Search/manage Obsidian notes | `/obsidian-vault` | `Find notes about X in Obsidian` | Search, create, organize vault notes |

---

## Meta: Skills About Skills

| I want to... | Skill | Prompt pattern | What it does |
|--------------|-------|---------------|-------------|
| Create a new custom skill | `/skill-creator` | `Create a skill for X` | Builds SKILL.md + supporting files |
| Turn a workflow into a skill | `workflow-skill-creator` | `Make this workflow a skill` | Distills completed workflow into reusable skill |
| Scaffold exercise structures | `/scaffold-exercises` | `Scaffold exercises for X` | Creates exercise dirs with problems/solutions |

---

## Quick Reference: "I have a task, which skill?"

| Task type | First choice | Why |
|-----------|-------------|-----|
| **Create implementation plan** | Built-in planning mode | Agent auto-creates `implementation_plan.md` + `task.md` — just describe what you want to build |
| **Break plan into tasks** | `/to-issues` | Converts PRD/plan into individual trackable issues |
| **Validate before building** | `/grill-me` | Catches bad assumptions before you invest time |
| **Write any PRD** | `/to-prd` | Structured output from raw conversation/doc |
| **Design any module** | `/codebase-design` | Deep module design with testing seams |
| **Choose between options** | `/design-an-interface` | Parallel sub-agents produce 2+ radically different designs |
| **Document a decision** | `/decision-mapping` | Investigation → resolution workflow |
| **Review anything** | `/review` | Standards + Spec compliance check |
| **Implement anything** | `/implement` or `/tdd` | `/implement` for speed, `/tdd` for correctness |
| **Debug anything** | `/diagnosing-bugs` | Structured diagnosis loop |
| **Deploy anything** | `/deploy-to-vercel` | One-command deployment |
| **Create any diagram** | `generate_image` | Professional PNG (not Mermaid) |
