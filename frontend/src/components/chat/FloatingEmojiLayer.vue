<template>
  <div v-if="isActive" class="pointer-events-none fixed inset-0 z-[140] overflow-hidden">
    <div class="absolute inset-0 bg-black/5 backdrop-blur-[2px]"></div>
    <span
      v-for="particle in particles"
      :key="particle.id"
      class="floating-emoji-particle"
      :style="particleStyle(particle)"
    >
      {{ particle.emoji }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref } from 'vue'
import { isCelebrationEmoji } from './emoji-catalog'

type ParticleKind = 'heart' | 'fire' | 'confetti' | 'sparkle'

type Particle = {
  id: number
  emoji: string
  kind: ParticleKind
  bornAt: number
  delay: number
  duration: number
  x: number
  y: number
  cp1x: number
  cp1y: number
  cp2x: number
  cp2y: number
  endX: number
  endY: number
  scale: number
  rotation: number
  rotationEnd: number
  opacity: number
  hueShift: number
}

const particles = ref<Particle[]>([])
const isActive = ref(false)
const frameTime = ref(typeof performance !== 'undefined' ? performance.now() : Date.now())
const prefersReducedMotion = typeof window !== 'undefined'
  ? window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches
  : false

let rafId = 0
let particleId = 0

const HEART_EMOJIS = ['❤️', '❤', '💖', '💘', '💗', '💓', '💞', '💕', '😍', '🥰']
const FIRE_EMOJIS = ['🔥']
const PARTY_EMOJIS = ['🎉']

function cubicPoint(a: number, b: number, c: number, d: number, t: number) {
  const mt = 1 - t
  return mt ** 3 * a + 3 * mt ** 2 * t * b + 3 * mt * t ** 2 * c + t ** 3 * d
}

function randomBetween(min: number, max: number) {
  return min + Math.random() * (max - min)
}

function particleKindForEmoji(emoji: string): ParticleKind {
  if (HEART_EMOJIS.includes(emoji)) return 'heart'
  if (FIRE_EMOJIS.includes(emoji)) return 'fire'
  if (PARTY_EMOJIS.includes(emoji)) return 'confetti'
  return 'sparkle'
}

function paletteForKind(kind: ParticleKind) {
  switch (kind) {
    case 'heart':
      return ['#fb7185', '#f43f5e', '#fecdd3']
    case 'fire':
      return ['#fb923c', '#f97316', '#facc15']
    case 'confetti':
      return ['#22c55e', '#38bdf8', '#f472b6', '#facc15']
    default:
      return ['#ffffff', '#dbeafe', '#c4b5fd']
  }
}

function createParticle(emoji: string, kind: ParticleKind, index: number, total: number): Particle {
  const viewportWidth = typeof window !== 'undefined' ? window.innerWidth : 390
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 844
  const wideSpread = kind === 'heart'
  const startX = viewportWidth * randomBetween(wideSpread ? 0.08 : 0.24, wideSpread ? 0.92 : 0.76)
  const startY = viewportHeight * randomBetween(wideSpread ? 0.52 : 0.68, wideSpread ? 0.9 : 0.84)
  const arc = kind === 'heart' ? randomBetween(220, 460) : randomBetween(120, 360)
  const spread = randomBetween(-120, 120) + (index - total / 2) * randomBetween(6, 14)
  const drift = randomBetween(-80, 80)
  const duration = prefersReducedMotion ? randomBetween(600, 900) : randomBetween(1400, 2200)
  const delay = randomBetween(0, kind === 'heart' ? 120 : 180)
  const scale = kind === 'confetti' ? randomBetween(0.7, 1.2) : randomBetween(0.85, 1.5)
  const rotation = randomBetween(-18, 18)
  const rotationEnd = rotation + randomBetween(-260, 260)
  const colors = paletteForKind(kind)

  return {
    id: ++particleId,
    emoji,
    kind,
    bornAt: performance.now(),
    delay,
    duration,
    x: startX,
    y: startY,
    cp1x: startX + randomBetween(-70, 70),
    cp1y: startY - arc * 0.32,
    cp2x: startX + drift + spread * 0.18,
    cp2y: startY - arc * 0.72,
    endX: startX + spread,
    endY: startY - arc - randomBetween(80, 180),
    scale,
    rotation,
    rotationEnd,
    opacity: randomBetween(0.78, 1),
    hueShift: kind === 'heart' ? 0 : randomBetween(-24, 24),
  }
}

function scheduleFrame() {
  cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(updateParticles)
}

function cleanupInactive(now: number) {
  particles.value = particles.value.filter((particle) => now - particle.bornAt <= particle.delay + particle.duration + 220)
  if (!particles.value.length) {
    isActive.value = false
    rafId = 0
  }
}

function updateParticles(now: number) {
  frameTime.value = now
  const nextParticles: Particle[] = []
  let stillActive = false

  for (const particle of particles.value) {
    const elapsed = now - particle.bornAt - particle.delay
    if (elapsed < 0) {
      nextParticles.push(particle)
      stillActive = true
      continue
    }

    const progress = Math.min(1, elapsed / particle.duration)
    if (progress >= 1) {
      continue
    }

    nextParticles.push(particle)
    stillActive = true
  }

  particles.value = nextParticles

  if (stillActive) {
    scheduleFrame()
    return
  }

  cleanupInactive(now)
}

function startLoop() {
  if (rafId) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(updateParticles)
}

function play(emoji: string, origin?: { x?: number; y?: number }) {
  const normalized = String(emoji || '').trim()
  if (!normalized) return

  const kind = particleKindForEmoji(normalized)
  const total = kind === 'heart' ? 36 : kind === 'fire' ? 24 : kind === 'confetti' ? 34 : 18
  const items: Particle[] = []

  for (let index = 0; index < total; index += 1) {
    const particle = createParticle(normalized, kind, index, total)
    if (origin?.x != null) particle.x = origin.x + randomBetween(-16, 16)
    if (origin?.y != null) particle.y = origin.y + randomBetween(-12, 12)
    items.push(particle)
  }

  particles.value = [...particles.value, ...items]
  isActive.value = true

  nextTick(() => {
    if (!rafId) startLoop()
  })
}

function particleStyle(particle: Particle) {
  const now = frameTime.value
  const elapsed = now - particle.bornAt - particle.delay

  if (elapsed < 0) {
    return {
      transform: `translate3d(${particle.x}px, ${particle.y}px, 0) scale(${particle.scale * 0.88})`,
      opacity: 0,
    }
  }

  const progress = Math.min(1, elapsed / particle.duration)
  const x = cubicPoint(particle.x, particle.cp1x, particle.cp2x, particle.endX, progress)
  const y = cubicPoint(particle.y, particle.cp1y, particle.cp2y, particle.endY, progress)
  const wobble = Math.sin(progress * Math.PI * 6) * (particle.kind === 'confetti' ? 6 : particle.kind === 'heart' ? 4 : 10)
  const scale = particle.scale * (1 + Math.sin(progress * Math.PI) * 0.16)
  const opacity = Math.max(0, particle.opacity * (1 - progress) * (progress < 0.12 ? progress / 0.12 : 1))
  const rotation = particle.rotation + (particle.rotationEnd - particle.rotation) * progress

  return {
    transform: `translate3d(${x}px, ${y + wobble}px, 0) rotate(${rotation}deg) scale(${scale})`,
    opacity,
    filter: `hue-rotate(${particle.hueShift}deg)`,
  }
}

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  rafId = 0
  particles.value = []
  isActive.value = false
})

defineExpose({
  play,
  playSpecial: play,
  triggerEmoji: play,
  trigger: play,
  isCelebrationEmoji,
})
</script>

<style scoped>
.floating-emoji-particle {
  position: absolute;
  left: 0;
  top: 0;
  will-change: transform, opacity, filter;
  transform-origin: center center;
  font-size: clamp(18px, 3vw, 34px);
  user-select: none;
  pointer-events: none;
  text-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
}
</style>
