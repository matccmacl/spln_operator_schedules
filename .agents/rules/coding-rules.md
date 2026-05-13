---
trigger: always_on
---

Behavioral guidelines to optimize coding output and minimize errors. Use these instructions to ensure precision, maintainability, and clarity in all generated artifacts.

**Core Philosophy:** Prioritize accuracy and surgical precision over broad, speculative changes.

## **1\. Pre-Computation Clarity**

**Eliminate ambiguity before generating code.**

Before starting a file block:

* **State Assumptions:** Explicitly list any assumptions about the tech stack or requirements.  
* **Surface Tradeoffs:** If a request has multiple valid implementations (e.g., performance vs. readability), present the options briefly.  
* **Ask First:** If the prompt is contradictory or missing critical data (like a missing API endpoint), stop and ask for clarification.

## **2\. Minimalist Architecture**

**Write the least amount of code necessary to fulfill the request.**

* **Feature Parity:** Do not add "nice-to-have" features or extra UI elements not explicitly requested.  
* **Single-Use Logic:** Avoid complex abstractions or "future-proofing" for code that is only intended for a specific task.  
* **Conciseness:** If logic can be expressed in 10 lines of clean code, do not use 50 lines of boilerplate.  
* **Senior Review:** Design the code such that a senior engineer would find it "elegant and simple" rather than "over-engineered."

## **3\. Surgical Implementation**

**Modify only the necessary lines. Respect the existing codebase.**

When editing an existing artifact:

* **Locality:** Only change the lines directly related to the fix or feature.  
* **Style Consistency:** Match the existing indentation, naming conventions, and architectural patterns perfectly.  
* **Cleanup Responsibility:** Only remove dead code or imports that *your* changes rendered obsolete. Do not perform unsolicited "spring cleaning" on the rest of the file.  
* **Diff Awareness:** Ensure every change is justifiable by the user's specific prompt.

## **4\. Verifiable Milestones**

**Define success through measurable goals.**

For any complex task, structure the execution:

1. **Plan:** Provide a 1-3 step roadmap of what will be implemented.  
2. **Implement:** Execute the code generation.  
3. **Verify:** Self-correct by checking if the implementation meets the "Success Criteria" (e.g., "The button now triggers the API," "The logic handles null values").

**Success Metric:** These guidelines are effective if the resulting files are clean, require zero immediate refactoring, and solve the user's problem with the first generation.