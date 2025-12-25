# Tasks

1. [x] Move `New Skill Creator Agent/skills/*` to `skills/`
2. [x] Move `New Skill Creator Agent/docs` to `docs/skills/`
3. [x] Move `New Skill Creator Agent/global-skill_creator.md` to `docs/skills/GUIDE.md`
4. [x] Delete `New Skill Creator Agent` directory
5. [x] Establish `openspec/specs/skill-creator/spec.md` with strict Rules.
   - Validation: `openspec validate` passes.
6. [ ] **Transform Skill to Agent**
   - [ ] Refactor `skills/skill-creator/SKILL.md` to be an Agent System Prompt.
     - Add "Role: Skill Architect".
     - Add "Generate -> Critique -> Revise" loop.
     - Embed "RULES" (No Auxiliaries, No TODOs).
   - [ ] Optimize `skills/skill-creator/references/` for Agent consumption.
7. [ ] **Validation & Integrity**
   - [ ] Verify `scripts/init_skill.py` aligns with Agent tools.
   - [ ] Verify `scripts/package_skill.py` is used as the "Definition of Done".
   - [ ] Test: Agent scaffolds a valid skill without human intervention.
