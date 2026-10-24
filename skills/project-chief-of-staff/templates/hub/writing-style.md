# Writing style for all outgoing content

Applies to everything a person outside the project will read: {{KINDS}}.
Goal: it reads like a capable person wrote it, not a model.

- **As you write:** a PostToolUse hook runs `tools/style_lint.py` on files in the outgoing folders ({{OUTGOING}}) and
  feeds any flags back. It never blocks.
- **Before anything is final:** `red-team-reviewer` runs `{{PY}} tools/style_lint.py <file>`. Nothing is final until the
  lint is clean or each remaining flag is justified in the review.

## Do
- Write plainly: say the specific thing, in ordinary words, at a natural length.
- Vary sentence length and structure the way speech does. Some short sentences. Some longer ones that carry detail.
- Use concrete nouns: {{CONCRETE}}.
- Match the register of the reader ({{RECIPIENTS}}) and the user's own voice.
- Use one idea per paragraph, and stop when it's said.

## Avoid (AI stylistic patterns)
- **Stock words and phrases:** delve, tapestry, testament to, ever-evolving, fast-paced world, navigate the complexities, embark,
  journey, realm, pivotal, foster, underscore, showcase, meticulous, intricate, multifaceted, seamless, cutting-edge, game-changer,
  unlock, synergy, leverage, robust, holistic, "I hope this email finds you well", "I am excited/thrilled to", "passionate about",
  "it's worth noting", "in conclusion", furthermore/moreover as connectors.
- **Shapes:** "not only X but also Y"; reflexive triplets ("innovative, scalable, and impactful"); a summary sentence restating
  the paragraph; opening with a rhetorical question; closing with a generic flourish.
- **Repetition:** the same sentence opener again and again (I… I… I…); identical paragraph rhythm; the same word reused
  within a few lines.
- **Typography tells:** frequent em dashes; exclamation marks; bold or bullets inside prose letters; Title Case Headings in emails.
- **Inflation:** adjectives standing in for evidence ("highly motivated", "world-class", "deeply passionate").

## Tone
Natural, direct, warm without gushing, confident without overclaiming. If a sentence could appear unchanged in anyone
else's version of this text, cut it or make it specific.
