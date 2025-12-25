What are skills? - Agent Skills

[Skip to main content](#content-area)

[Agent Skills home page

Agent Skills](/)

Search...

⌘K

* [agentskills/agentskills](https://github.com/agentskills/agentskills)
* [agentskills/agentskills](https://github.com/agentskills/agentskills)

Search...

Navigation

What are skills?

* [Overview](/home)

* [What are skills?](/what-are-skills)

* [Specification](/specification)

* [Integrate skills](/integrate-skills)

On this page

* [How skills work](#how-skills-work)
* [The SKILL.md file](#the-skill-md-file)
* [Next steps](#next-steps)

# What are skills?

Copy page

Agent Skills are a lightweight, open format for extending AI agent capabilities with specialized knowledge and workflows.

Copy page

At its core, a skill is a folder containing a `SKILL.md` file. This file includes metadata (`name` and `description`, at minimum) and instructions that tell an agent how to perform a specific task. Skills can also bundle scripts, templates, and reference materials.

Report incorrect code

Copy

Ask AI

```
my-skill/
├── SKILL.md          # Required: instructions + metadata
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
```

## [​](#how-skills-work) How skills work

Skills use **progressive disclosure** to manage context efficiently:

1. **Discovery**: At startup, agents load only the name and description of each available skill, just enough to know when it might be relevant.
2. **Activation**: When a task matches a skill’s description, the agent reads the full `SKILL.md` instructions into context.
3. **Execution**: The agent follows the instructions, optionally loading referenced files or executing bundled code as needed.

This approach keeps agents fast while giving them access to more context on demand.

## [​](#the-skill-md-file) The SKILL.md file

Every skill starts with a `SKILL.md` file containing YAML frontmatter and Markdown instructions:

Report incorrect code

Copy

Ask AI

```
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents.
---

# PDF Processing

## When to use this skill
Use this skill when the user needs to work with PDF files...

## How to extract text
1. Use pdfplumber for text extraction...

## How to fill forms
...
```

The following frontmatter is required at the top of `SKILL.md`:

* `name`: A short identifier
* `description`: When to use this skill

The Markdown body contains the actual instructions and has no specific restrictions on structure or content.
This simple format has some key advantages:

* **Self-documenting**: A skill author or user can read a `SKILL.md` and understand what it does, making skills easy to audit and improve.
* **Extensible**: Skills can range in complexity from just text instructions to executable code, assets, and templates.
* **Portable**: Skills are just files, so they’re easy to edit, version, and share.

## [​](#next-steps) Next steps

* [View the specification](/specification) to understand the full format.
* [Add skills support to your agent](/integrate-skills) to build a compatible client.
* [See example skills](https://github.com/anthropics/skills) on GitHub.
* [Read authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) for writing effective skills.
* [Use the reference library](https://github.com/agentskills/agentskills/tree/main/skills-ref) to validate skills and generate prompt XML.

[Overview](/home)[Specification](/specification)

⌘I

[Powered by Mintlify](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=agent-skills)