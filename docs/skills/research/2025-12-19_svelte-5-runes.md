# Research: Svelte 5 Runes

**Date**: 2025-12-19
**Context**: Verification mechanism for Deep Research Workflow. Grounding on "Svelte 5 Runes".

## Executive Summary

Runes represent a paradigm shift in Svelte 5 from implicit, compile-time reactivity (Svelte 4) to **explicit, fine-grained reactivity** based on signals. This change unifies state management across components and plain JS files (`.svelte.js`), eliminates the need for strict store abstractions, and optimizes performance by ensuring only granular dependencies trigger updates.

## Technical Deep Dive (Perplexity)

**Core Concepts:**

- **Opt-in**: Runes are opt-in. Legacy syntax works but Runes are preferred for new code.
- **Signals**: Under the hood, Svelte 5 uses signals. Runes are the public API for these signals.
- **Fine-Grained**: Updates are precise. Changing a property in an object/array only invalidates that specific property, not the whole structure.
- **Universal**: Runes work in `.svelte.js` files, allowing "global state" without `writable` stores.

**Architecture Patterns:**

- **State**: Use `$state(initialValue)` for local component state.
- **Derived**: Use `$derived(expression)` for values computed from state. Replaces `$:`.
- **Props**: Use `let { prop } = $props()` to destructure props. Replaces `export let prop`.
- **Effects**: Use `$effect(() => {})` for side effects. Runs only in the browser. Replaces `onMount` / `afterUpdate` largely.

## API & Implementation Reference (Context7)

### Defining State

```svelte
<script>
  // Svelte 5
  let count = $state(0);

  // Array mutation is fine-grained
  let items = $state([1, 2, 3]);

  function increment() {
    count += 1; // Works plainly
    items[0] = 99; // Triggers update ONLY for index 0
  }
</script>
```

### Derived Values

```svelte
<script>
  let count = $state(0);
  // Replaces $: double = count * 2
  const double = $derived(count * 2);
</script>
```

### Props

```svelte
<script>
  // Replaces export let name;
  let { name, age = 25 } = $props();
</script>
```

### Bridge to Stores

If you must integrate with legacy stores:

```javascript
import { toStore, fromStore } from "svelte/store";

let count = $state(0);
const countStore = toStore(
  () => count,
  (v) => (count = v)
);
```

## Action Plan

- [x] Verified Perplexity retrieval.
- [x] Verified Context7 retrieval.
- [x] Generated grounded documentation.
