<!-- MathRenderer.vue -->
<template>
  <span ref="mathElement" class="math-content">
    <slot v-if="!content">{{ defaultContent }}</slot>
    <span v-else>{{ content }}</span>
  </span>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps<{
  content?: string
  display?: boolean
}>()

const mathElement = ref<HTMLElement | null>(null)
const defaultContent = ref('')

// Function to check if text contains LaTeX math
function hasLatex(text: string): boolean {
  return /\\\(|\\\[|\\\\|\\frac|\\sqrt|\\sum|\\int|\\alpha|\\beta|\\gamma|\\delta|\\theta|\\lambda|\\mu|\\pi|\\sigma|\\phi|\\omega|\\Delta|\\Sigma|\\Omega|_|\^/.test(text)
}

// Matches an actual LaTeX token: a backslash command optionally followed by
// up to two brace groups (covers \Delta, \longrightarrow, \sqrt{x}, \frac{a}{b},
// \vec{F}, etc.), or a bare subscript/superscript (H_{2}, x^2, k^{-1}).
const LATEX_TOKEN_RE = /\\[a-zA-Z]+(?:\{[^{}]*\}){0,2}|[_^](?:\{[^{}]*\}|[a-zA-Z0-9])/g

// Escape characters that are special to TeX so plain English text renders
// literally instead of being (mis)interpreted as math syntax.
function escapeForKatexText(segment: string): string {
  return segment.replace(/[{}$%#&~]/g, '\\$&')
}

// The backend embeds raw LaTeX commands directly inside otherwise-plain
// sentences (e.g. "the flux due to a point source ... \Delta H = 240kJmol-1")
// rather than delimiting math with \( \) or $ $. Feeding a string like that
// straight into katex.render() treats the ENTIRE sentence as one math
// expression: every word becomes an italic math variable and inter-word
// spacing collapses (KaTeX ignores whitespace between bare identifiers in
// math mode). To fix that, we split the string into "real LaTeX token" runs
// (left untouched, so \Delta / \sqrt{..} / subscripts still render as math)
// and "plain text" runs in between, which get wrapped in \text{...} so KaTeX
// renders them upright with normal word spacing, just like ordinary prose.
function buildKatexSource(text: string): string {
  // Multi-line stems: \text{} doesn't handle literal newlines, so collapse
  // them to a single space for this inline preview rendering.
  const flat = text.replace(/\s*\n+\s*/g, ' ')

  let result = ''
  let lastIndex = 0
  let match: RegExpExecArray | null
  LATEX_TOKEN_RE.lastIndex = 0
  while ((match = LATEX_TOKEN_RE.exec(flat)) !== null) {
    const plain = flat.slice(lastIndex, match.index)
    if (plain) result += `\\text{${escapeForKatexText(plain)}}`
    result += match[0]
    lastIndex = match.index + match[0].length
  }
  const rest = flat.slice(lastIndex)
  if (rest) result += `\\text{${escapeForKatexText(rest)}}`
  return result
}

function renderMath() {
  if (!mathElement.value) return
  
  const el = mathElement.value
  let text = props.content || el.textContent || ''
  
  // If content is empty, try to get from slot
  if (!text && el.children.length > 0) {
    text = el.textContent || ''
  }
  
  if (!text || !hasLatex(text)) {
    // If no LaTeX, just show plain text
    return
  }
  
  // If KaTeX is available
  if (window.katex) {
    try {
      // Clear the element
      el.innerHTML = ''
      const katexSource = buildKatexSource(text)
      window.katex.render(katexSource, el, {
        displayMode: props.display || false,
        throwOnError: false,
        trust: true,
        macros: {
          "\\R": "\\mathbb{R}",
          "\\N": "\\mathbb{N}",
          "\\Z": "\\mathbb{Z}",
          "\\Q": "\\mathbb{Q}",
          "\\deg": "\\text{deg}",
        }
      })
      return
    } catch (e) {
      console.warn('KaTeX rendering failed for:', text, e)
    }
  }
  
  // Fallback: show text with preserved formatting
  el.textContent = text
}

onMounted(() => {
  nextTick(renderMath)
})

watch(() => props.content, () => {
  nextTick(renderMath)
})
</script>

<style scoped>
/* Global styles for math rendering */
.math-content {
  font-family: 'Times New Roman', 'Computer Modern', serif;
  font-style: normal !important;
}

.math-content .katex {
  font-family: 'KaTeX_Main', 'Times New Roman', serif;
  font-style: normal !important;
}

.math-content .katex .mathnormal {
  font-style: italic !important;
}

/* For non-math text in math renderer */
.math-content:not(:has(.katex)) {
  font-family: inherit;
  font-style: normal !important;
}

/* Question text normal font */
.question-text {
  font-family: 'Times New Roman', serif;
  font-style: normal;
  font-weight: normal;
}

/* Option text normal font */
.option-text {
  font-family: 'Times New Roman', serif;
  font-style: normal;
  font-weight: normal;
}
</style>